from core.domain.errors import AccountDisabled, OAuthProviderNotFound, UserNotFound
from core.domain.entities import User, SocialIdentity
from core.domain.value_objects import ImageRef, OAuthProvider, Role 
from core.ports.clock import Clock
from core.ports.security import TokenService, TokenPair
from core.ports.repositories import UserRepository, SocialIdentityRepository
from core.ports.oauth_provider import OAuthProviderPort, ExternalOAuthProvider
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
        print("Step 2: Usecase of OAuth")
        provider_service = self.providers.get(provider)
        if not provider_service:
            print("Step 3: Provider not found:")
            raise OAuthProviderNotFound(f"Unsupported OAuth provider: {provider}")
        print("Step 3: Provider found:", provider_service)
        print("Step 4: Fetch user profile data.")
        profile = provider_service.fetch_user_profile(code, redirect_url)
        with self.uow :
            print("Step 5: Check for existing social identity")
            user = self._resolve_or_create_user(profile)
            if not user.is_active :
                raise AccountDisabled()
            print("Step 9: Issue Access Token and Refresh Token")
            pair = self.tokens.issue(user)
            self.users.touch_last_login(user.id, self.clock.now())
            self.uow.commit()
        print("Step 10: Return user")
        print(user)
        return user, pair

    def _resolve_or_create_user(self, profile: ExternalOAuthProvider) -> User :
        identity = self.socialidentities.get_by_provider_and_id(provider=profile.provider, provider_user_id=profile.provider_user_id)

        if identity :
            print("Step 6: If Identity exist check for user")
            user = self.users.get(identity.User_id)

            if not user :
                print("Step 7: If user not exist raise error")
                raise UserNotFound("User record missing for existing social identity")
            print("Step 7: User exist return user")
            print(user)
            return user
        print("Step 6: Identity not exist, checking for user exist")
        user = self.users.get_by_email(profile.email)
        if not user :
            username = profile.email.split("@")[0].strip()
            avatar = ImageRef("oauth", profile.avater_url) if profile.avater_url else None
            phone = None

            user = User(
                id=None,
                username=username,
                email=profile.email,
                first_name=profile.first_name.strip(),
                last_name=profile.last_name.strip(),
                phone=phone,
                role=Role.USER,
                is_verified=True,
                is_active=True,
                avatar=avatar,
                date_joined=self.clock.now(),
            )
            user = self.users.add(use=user, password=None)
            print("Step 7: User not exist so create user")
            print(user)
        print("Step 8: Create a new identity for user")
        new_identity = SocialIdentity(
            id=None,
            User_id=user.id,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            created=self.clock.now()                
        )
        self.socialidentities.add(new_identity)

        return user