"""Fake infrastructure adapters."""

from datetime import UTC, date, datetime, timedelta

from core.domain.entities import Post, User
from core.domain.errors import InvalidToken
from core.domain.ids import UserId
from core.domain.periods import LEADERBOARD_TZ
from core.domain.value_objects import ImageRef, OTPPurpose, Role
from core.ports.clock import Clock
from core.ports.notifications import Notifier
from core.ports.security import PasswordHasher, TokenClaims, TokenPair, TokenService
from core.ports.storage import ImageStorage
from core.ports.unit_of_work import UnitOfWork


class FakeClock(Clock):
    def __init__(self, at: datetime | None = None) -> None:
        self._now = at or datetime(2026, 7, 17, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def today_local(self) -> date:
        return self._now.astimezone(LEADERBOARD_TZ).date()

    def advance(self, **kwargs) -> None:
        self._now += timedelta(**kwargs)

    def set(self, at: datetime) -> None:
        self._now = at


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.commits = 0

    def commit(self) -> None:
        self.committed = True
        self.commits += 1

    def rollback(self) -> None:
        self.rolled_back = True


class FakeImageStorage(ImageStorage):
    def __init__(self, fail_upload: bool = False) -> None:
        self.uploaded: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self.fail_upload = fail_upload
        self._seq = 0

    def upload(self, data: bytes, filename: str, content_type: str) -> ImageRef:
        if self.fail_upload:
            from core.domain.errors import ImageUploadFailed

            raise ImageUploadFailed()
        self._seq += 1
        external_id = f"fake-{self._seq}"
        self.uploaded[external_id] = data
        return ImageRef(provider="fake", external_id=external_id)

    def delete(self, ref: ImageRef) -> None:
        self.deleted.append(ref.external_id)
        self.uploaded.pop(ref.external_id, None)

    def public_url(self, ref: ImageRef) -> str:
        return f"https://fake.local/{ref.external_id}"


class FakeNotifier(Notifier):
    def __init__(self) -> None:
        self.otps: list[tuple[str, int, OTPPurpose]] = []
        self.approvals: list[tuple[str, Post]] = []
        self.rejections: list[tuple[str, Post, str]] = []

    def send_otp(self, to: str, code: int, purpose: OTPPurpose) -> None:
        self.otps.append((to, code, purpose))

    def send_post_approved(self, to: str, post: Post) -> None:
        self.approvals.append((to, post))

    def send_post_rejected(self, to: str, post: Post, reason: str) -> None:
        self.rejections.append((to, post, reason))


class FakePasswordHasher(PasswordHasher):
    def hash(self, raw: str) -> str:
        return f"hashed::{raw}"

    def verify(self, raw: str, hashed: str) -> bool:
        return hashed == f"hashed::{raw}"


class FakeTokenService(TokenService):
    def __init__(self, clock: Clock) -> None:
        self.clock = clock
        self.revoked: set[str] = set()
        self._seq = 0

    def issue(self, user: User) -> TokenPair:
        assert user.id is not None
        self._seq += 1
        return TokenPair(
            access=f"access::{user.id}::{user.role}::{self._seq}",
            refresh=f"refresh::{user.id}::{user.role}::{self._seq}",
            access_expires_at=self.clock.now() + timedelta(minutes=15),
        )

    def _parse(self, token: str, expected: str) -> TokenClaims:
        if token in self.revoked:
            raise InvalidToken()
        parts = token.split("::")
        if len(parts) != 4 or parts[0] != expected:
            raise InvalidToken()
        return TokenClaims(
            user_id=UserId(int(parts[1])),
            role=Role(parts[2]),
            expires_at=self.clock.now() + timedelta(minutes=15),
            jti=parts[3],
        )

    def verify_access(self, token: str) -> TokenClaims:
        return self._parse(token, "access")

    def verify_refresh(self, token: str) -> TokenClaims:
        return self._parse(token, "refresh")

    def rotate(self, refresh_token: str) -> TokenPair:
        claims = self.verify_refresh(refresh_token)
        self.revoked.add(refresh_token)
        self._seq += 1
        return TokenPair(
            access=f"access::{claims.user_id}::{claims.role}::{self._seq}",
            refresh=f"refresh::{claims.user_id}::{claims.role}::{self._seq}",
            access_expires_at=self.clock.now() + timedelta(minutes=15),
        )

    def revoke(self, refresh_token: str) -> None:
        self.revoked.add(refresh_token)  # idempotent
