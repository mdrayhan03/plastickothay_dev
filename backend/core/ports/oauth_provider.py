from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.domain.value_objects import OAuthProvider

@dataclass(frozen=True)
class ExternalOAuthProvider :
    provider: OAuthProvider
    provider_user_id: str
    email: str
    phone: str
    first_name: str
    last_name: str
    avater_url: str

class OAuthProviderPort(ABC) :
    @abstractmethod
    def fetch_user_profile(self, code: str, redirect_uri: str) -> ExternalOAuthProvider :
        """Exchanges auth code with the 3rd party provider and returns normalized user info."""