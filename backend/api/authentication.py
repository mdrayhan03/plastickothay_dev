"""Cookie/header-aware JWT authentication.

Access token arrives as `Authorization: Bearer <token>`. Critically, when NO token is present
this returns None rather than raising — so anonymous requests reach AllowAny endpoints (the
public map, report submission) instead of being 401'd at the door (LLD §8.1, §8.2).

request.user is a lightweight DomainUser carrying id and role from the token claims; it does
not hit the database. Views that need the full profile load it through a use case.
"""

from rest_framework.authentication import BaseAuthentication, get_authorization_header

from core.domain.errors import InvalidToken
from core.domain.ids import UserId
from core.domain.value_objects import Role
from core.ports.security import TokenClaims


class DomainUser:
    """The object DRF stores on request.user for an authenticated caller."""

    is_authenticated = True

    is_anonymous = False

    def __init__(self, claims: TokenClaims) -> None:
        self.id = claims.user_id
        self.pk = claims.user_id  # DRF throttling reads request.user.pk for the cache key
        self.role = claims.role

    @property
    def is_staff(self) -> bool:
        return self.role in (Role.STAFF, Role.ADMIN)

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    def __str__(self) -> str:
        return f"DomainUser(id={self.id}, role={self.role})"


def actor_id(request) -> UserId | None:
    """The authenticated user's id, or None for anonymous. Use this in views."""
    user = getattr(request, "user", None)
    return getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None


class JWTCookieAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def __init__(self):
        from adapters.security.jwt_service import SimpleJWTTokenService

        self.tokens = SimpleJWTTokenService()

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != self.keyword:
            return None  # anonymous — not an error
        if len(header) != 2:
            from rest_framework.exceptions import AuthenticationFailed

            raise AuthenticationFailed("Malformed Authorization header.")

        try:
            claims = self.tokens.verify_access(header[1].decode())
        except InvalidToken as exc:
            from rest_framework.exceptions import AuthenticationFailed

            raise AuthenticationFailed("Invalid or expired token.") from exc
        return DomainUser(claims), None

    def authenticate_header(self, request):
        return "Bearer"
