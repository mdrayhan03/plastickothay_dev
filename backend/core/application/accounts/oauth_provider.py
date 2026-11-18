from core.domain.entities import SocialIdentity, User
from core.domain.errors import AccountDisabled, OAuthProviderNotFound, UserNotFound
from core.domain.value_objects import ImageRef, OAuthProvider, Role
from core.ports.clock import Clock
from core.ports.oauth_provider import ExternalOAuthProvider, OAuthProviderPort
from core.ports.repositories import SocialIdentityRepository, UserRepository
from core.ports.security import TokenPair, TokenService
from core.ports.unit_of_work import UnitOfWork


class AuthenticateOAuth:
    def __init__(
            self,
            providers: dict[OAuthProvider, OAuthProviderPort],
            socialidentities: SocialIdentityRepository,
            users: UserRepository,
            clock: Clock,
            tokens: TokenService,
            uow: UnitOfWork
    ):
        self.providers = providers
        self.socialidentities = socialidentities
        self.users = users
        self.clock = clock
        self.tokens = tokens
        self.uow = uow

    def execute(
            self,
            provider: OAuthProvider,
            code: str,
            redirect_url: str
    ) -> tuple[User, TokenPair]:
        provider_service = self.providers.get(provider)
        if not provider_service:
            raise OAuthProviderNotFound(f"Unsupported OAuth provider: {provider}")
        profile = provider_service.fetch_user_profile(code, redirect_url)
        with self.uow :
            user = self._resolve_or_create_user(profile)
            if not user.is_active :
                raise AccountDisabled()
            pair = self.tokens.issue(user)
            self.users.touch_last_login(user.id, self.clock.now())
            self.uow.commit()
        return user, pair

    def _resolve_or_create_user(self, profile: ExternalOAuthProvider) -> User :
        identity = self.socialidentities.get_by_provider_and_id(provider=profile.provider, provider_user_id=profile.provider_user_id)

        if identity :
            user = self.users.get(identity.User_id)

            if not user :
                raise UserNotFound("User record missing for existing social identity")
            return user
        user = self.users.get_by_email(profile.email)
        if not user :
            username = profile.email.split("@")[0].strip()
            avatar = ImageRef("oauth", profile.avater_url) if profile.avater_url else None

            user = User(
                id=None,
                username=username,
                email=profile.email,
                first_name=profile.first_name.strip(),
                last_name=profile.last_name.strip(),
                phone=profile.phone.strip(),
                role=Role.USER,
                is_verified=True,
                is_active=True,
                avatar=avatar,
                date_joined=self.clock.now(),
            )
            user = self.users.add(user=user, password=None)
            
        new_identity = SocialIdentity(
            id=None,
            User_id=user.id,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            created=self.clock.now()                
        )
        self.socialidentities.create(new_identity)

        return user