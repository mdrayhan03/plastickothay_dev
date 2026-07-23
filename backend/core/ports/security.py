"""Security ports — tokens and password hashing.

Implemented by SimpleJWT and Django's hashers respectively. The domain knows a token is an
opaque string with claims; it does not know what JWT is.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from core.domain.entities import User
from core.domain.ids import UserId
from core.domain.value_objects import Role


@dataclass(frozen=True, slots=True)
class TokenPair:
    access: str
    refresh: str
    access_expires_at: datetime


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: UserId
    role: Role
    expires_at: datetime
    jti: str


class TokenService(ABC):
    @abstractmethod
    def issue(self, user: User) -> TokenPair: ...

    @abstractmethod
    def verify_access(self, token: str) -> TokenClaims:
        """Raises InvalidToken."""

    @abstractmethod
    def verify_refresh(self, token: str) -> TokenClaims:
        """Raises InvalidToken."""

    @abstractmethod
    def rotate(self, refresh_token: str) -> TokenPair:
        """Issue a new pair and blacklist the old refresh token. Raises InvalidToken."""

    @abstractmethod
    def revoke(self, refresh_token: str) -> None:
        """Blacklist a refresh token. Idempotent — revoking twice is not an error."""


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, raw: str) -> str: ...

    @abstractmethod
    def verify(self, raw: str, hashed: str) -> bool: ...
