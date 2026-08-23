"""Registration and OTP verification.

Ports the legacy flow (superadmin/views.py:90-137) with two corrections:
  - `is_active` and `is_verified` are separated. The legacy model defaulted `is_active=False`
    and used it to gate unverified accounts, conflating "not yet verified" with "banned"
    (LLD §9.1). Here `is_verified` gates sign-in; `is_active` means not banned.
  - OTP expiry is checked on read. The legacy TTL index was a Mongo feature; Postgres has
    none, so correctness must never depend on a cleanup job running (LLD §9.4).
"""

import secrets
from datetime import timedelta

from core.application.accounts.avatars import upload_avatar
from core.application.accounts.dto import RegisterCommand, VerifyOTPCommand
from core.domain.entities import OTP, User
from core.domain.errors import EmailTaken, OTPExpired, OTPInvalid, UsernameTaken, UserNotFound
from core.domain.value_objects import OTPPurpose, Role
from core.ports.clock import Clock
from core.ports.notifications import Notifier
from core.ports.repositories import OTPRepository, UserRepository
from core.ports.storage import ImageStorage
from core.ports.unit_of_work import UnitOfWork

OTP_TTL = timedelta(minutes=3)
OTP_MIN = 100_000
OTP_MAX = 999_999


def generate_otp() -> int:
    # secrets, not random: this code guards account takeover.
    return secrets.randbelow(OTP_MAX - OTP_MIN + 1) + OTP_MIN


class _OTPIssuer:
    def __init__(self, otps: OTPRepository, notifier: Notifier, clock: Clock) -> None:
        self.otps = otps
        self.notifier = notifier
        self.clock = clock

    def issue(self, username: str, email: str, purpose: OTPPurpose) -> OTP:
        now = self.clock.now()
        self.otps.purge_expired(now)  # opportunistic cleanup - no scheduler available
        self.otps.invalidate_for(username, purpose)  # only the newest code is ever valid
        otp = self.otps.add(
            OTP(
                id=None,
                username=username,
                code=generate_otp(),
                purpose=purpose,
                created_at=now,
                expires_at=now + OTP_TTL,
            )
        )
        self.notifier.send_otp(email, otp.code, purpose)
        return otp


class RegisterUser:
    def __init__(
        self,
        users: UserRepository,
        otps: OTPRepository,
        notifier: Notifier,
        uow: UnitOfWork,
        clock: Clock,
        images: ImageStorage | None = None,
    ) -> None:
        self.users = users
        self.issuer = _OTPIssuer(otps, notifier, clock)
        self.uow = uow
        self.clock = clock
        self.images = images

    def execute(self, cmd: RegisterCommand) -> User:
        username = cmd.username.strip().lower()
        email = cmd.email.strip().lower()

        if self.users.get_by_username(username) is not None:
            raise UsernameTaken()
        if self.users.get_by_email(email) is not None:
            raise EmailTaken()

        avatar = upload_avatar(self.images, cmd.avatar)

        with self.uow:
            user = self.users.add(
                User(
                    id=None,
                    username=username,
                    email=email,
                    first_name=cmd.first_name.strip(),
                    last_name=cmd.last_name.strip(),
                    phone=cmd.phone.strip(),
                    role=Role.USER,
                    is_verified=False,
                    is_active=True,
                    avatar=avatar,
                    date_joined=self.clock.now(),
                ),
                password=cmd.password,
            )
            self.uow.commit()

        # After commit: Mailjet is synchronous (no Celery), and a mail failure must not
        # roll back a created account - the user can request a fresh code.
        self.issuer.issue(user.username, user.email, OTPPurpose.REGISTRATION)
        return user


class VerifyOTP:
    def __init__(
        self,
        users: UserRepository,
        otps: OTPRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.users = users
        self.otps = otps
        self.uow = uow
        self.clock = clock

    def execute(self, cmd: VerifyOTPCommand) -> User:
        username = cmd.username.strip().lower()
        user = self.users.get_by_username(username)
        if user is None:
            raise UserNotFound()

        now = self.clock.now()
        otp = self.otps.latest_valid_for(username, OTPPurpose.REGISTRATION, now)
        if otp is None:
            raise OTPInvalid()
        if otp.is_expired(now):
            raise OTPExpired()
        if not otp.matches(cmd.code):
            raise OTPInvalid()

        with self.uow:
            user.is_verified = True
            updated = self.users.update(user)
            self.otps.invalidate_for(username, OTPPurpose.REGISTRATION)
            self.uow.commit()
        return updated


class ResendOTP:
    def __init__(
        self,
        users: UserRepository,
        otps: OTPRepository,
        notifier: Notifier,
        clock: Clock,
    ) -> None:
        self.users = users
        self.issuer = _OTPIssuer(otps, notifier, clock)

    def execute(self, username: str, purpose: OTPPurpose = OTPPurpose.REGISTRATION) -> None:
        user = self.users.get_by_username(username.strip().lower())
        if user is None:
            # Silent success: a different response here would let anyone enumerate accounts.
            return
        self.issuer.issue(user.username, user.email, purpose)
