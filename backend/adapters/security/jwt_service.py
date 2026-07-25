"""JWT token service - SimpleJWT behind the TokenService port.

Access tokens are short and stateless; refresh tokens are revocable via SimpleJWT's blacklist
app (installed in B1). That blacklist is what makes logout real - without server state, logout
would only mean "the client forgot" (LLD §8.1).

The domain's TokenClaims carry role so permission checks never re-hit the DB for it.
"""

from datetime import timedelta

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from core.domain.entities import User
from core.domain.errors import InvalidToken
from core.domain.ids import UserId
from core.domain.value_objects import Role
from core.ports.security import TokenClaims, TokenPair, TokenService

ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=7)
ROLE_CLAIM = "role"


class SimpleJWTTokenService(TokenService):
    def issue(self, user: User) -> TokenPair:
        assert user.id is not None
        refresh = RefreshToken()
        refresh["user_id"] = int(user.id)
        refresh[ROLE_CLAIM] = user.role.value
        refresh.set_exp(lifetime=REFRESH_TTL)

        access = refresh.access_token
        access.set_exp(lifetime=ACCESS_TTL)

        return TokenPair(
            access=str(access),
            refresh=str(refresh),
            access_expires_at=self._exp(access),
        )

    def verify_access(self, token: str) -> TokenClaims:
        try:
            return self._claims(AccessToken(token))
        except TokenError as exc:
            raise InvalidToken() from exc

    def verify_refresh(self, token: str) -> TokenClaims:
        try:
            return self._claims(RefreshToken(token))
        except TokenError as exc:
            raise InvalidToken() from exc

    def rotate(self, refresh_token: str) -> TokenPair:
        try:
            old = RefreshToken(refresh_token)
            old.check_blacklist()  # a revoked token cannot be rotated
        except TokenError as exc:
            raise InvalidToken() from exc

        old.blacklist()  # blacklist-after-rotation: the old refresh is now dead

        new = RefreshToken()
        new["user_id"] = old["user_id"]
        new[ROLE_CLAIM] = old.get(ROLE_CLAIM, Role.USER.value)
        new.set_exp(lifetime=REFRESH_TTL)
        access = new.access_token
        access.set_exp(lifetime=ACCESS_TTL)
        return TokenPair(access=str(access), refresh=str(new), access_expires_at=self._exp(access))

    def revoke(self, refresh_token: str) -> None:
        import contextlib

        # Already invalid/expired - revoking is idempotent.
        with contextlib.suppress(TokenError):
            RefreshToken(refresh_token).blacklist()

    def _claims(self, token) -> TokenClaims:
        return TokenClaims(
            user_id=UserId(int(token["user_id"])),
            role=Role(token.get(ROLE_CLAIM, Role.USER.value)),
            expires_at=self._exp(token),
            jti=token.get("jti", ""),
        )

    def _exp(self, token):
        from datetime import UTC, datetime

        return datetime.fromtimestamp(token["exp"], tz=UTC)
