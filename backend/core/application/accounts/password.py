"""Password reset via OTP."""

from core.application.accounts.dto import ResetPasswordCommand
from core.application.accounts.registration import _OTPIssuer
from core.domain.errors import OTPExpired, OTPInvalid, UserNotFound
from core.domain.value_objects import OTPPurpose
from core.ports.clock import Clock
from core.ports.notifications import Notifier
from core.ports.repositories import OTPRepository, UserRepository
from core.ports.unit_of_work import UnitOfWork


class RequestPasswordReset:
    def __init__(
        self,
        users: UserRepository,
        otps: OTPRepository,
        notifier: Notifier,
        clock: Clock,
    ) -> None:
        self.users = users
        self.issuer = _OTPIssuer(otps, notifier, clock)

    def execute(self, username: str) -> None:
        user = self.users.get_by_username(username.strip().lower())
        if user is None:
            # Silent success: distinguishing here would leak which accounts exist.
            return
        self.issuer.issue(user.username, user.email, OTPPurpose.PASSWORD_RESET)


class ResetPassword:
    def __init__(
        self,
        users: UserRepository,
        otps: OTPRepository,
        tokens,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.users = users
        self.otps = otps
        self.tokens = tokens
        self.uow = uow
        self.clock = clock

    def execute(self, cmd: ResetPasswordCommand) -> None:
        username = cmd.username.strip().lower()
        user = self.users.get_by_username(username)
        if user is None or user.id is None:
            raise UserNotFound()

        now = self.clock.now()
        otp = self.otps.latest_valid_for(username, OTPPurpose.PASSWORD_RESET, now)
        if otp is None:
            raise OTPInvalid()
        if otp.is_expired(now):
            raise OTPExpired()
        if not otp.matches(cmd.code):
            raise OTPInvalid()

        with self.uow:
            self.users.set_password(user.id, cmd.new_password)
            self.otps.invalidate_for(username, OTPPurpose.PASSWORD_RESET)
            self.uow.commit()
