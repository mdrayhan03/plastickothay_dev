"""Login, token refresh, and logout.

Sessions are gone: the legacy flow set `request.session['user_id']` plus a `remember_me`
cookie. Tokens replace both. Logout is real here — revoking the refresh token is server-side
state, without which "logout" would only mean "the client forgot" (LLD §8.1).
"""

from core.application.accounts.dto import LoginCommand
from core.domain.entities import User
from core.domain.errors import AccountDisabled, AccountNotVerified, InvalidCredentials
from core.ports.clock import Clock
from core.ports.repositories import UserRepository
from core.ports.security import TokenPair, TokenService


class Login:
    def __init__(self, users: UserRepository, tokens: TokenService, clock: Clock) -> None:
        self.users = users
        self.tokens = tokens
        self.clock = clock

    def execute(self, cmd: LoginCommand) -> tuple[User, TokenPair]:
        user = self.users.get_by_username(cmd.username.strip().lower())
        if user is None or user.id is None:
            raise InvalidCredentials()
        if not self.users.verify_password(user.id, cmd.password):
            raise InvalidCredentials()

        # Checked only after the password: answering "not verified" to a wrong password
        # would confirm the account exists.
        if not user.is_verified:
            raise AccountNotVerified()
        if not user.is_active:
            raise AccountDisabled()

        pair = self.tokens.issue(user)
        self.users.touch_last_login(user.id, self.clock.now())
        return user, pair


class RefreshToken:
    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self.users = users
        self.tokens = tokens

    def execute(self, refresh_token: str) -> TokenPair:
        claims = self.tokens.verify_refresh(refresh_token)
        user = self.users.get(claims.user_id)
        if user is None or not user.can_sign_in:
            # A user banned mid-session must not be able to refresh their way back in.
            raise AccountDisabled()
        return self.tokens.rotate(refresh_token)


class Logout:
    def __init__(self, tokens: TokenService) -> None:
        self.tokens = tokens

    def execute(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return  # already logged out; not an error
        self.tokens.revoke(refresh_token)
