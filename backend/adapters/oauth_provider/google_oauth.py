import os

import requests

from core.domain.entities import OAuthProvider
from core.domain.errors import GoogleOAuthError
from core.ports.oauth_provider import ExternalOAuthProvider, OAuthProviderPort


def _credentials() :
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    return GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET

class GoogleOAuthProvider(OAuthProviderPort) :
    def __init__(self):
        self.client_id, self.client_secret = _credentials()

    def fetch_user_profile(self, code: str, redirect_uri: str) -> ExternalOAuthProvider:
        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        print("Token:", token_res.text)
        if token_res.status_code != 200 :
            raise GoogleOAuthError()
        
        tokens = token_res.json()
        access_token = tokens["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Fetch userinfo from Google API
        userinfo_res = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers=auth_headers,
            timeout=10,
        )

        if userinfo_res.status_code != 200 :
            raise GoogleOAuthError()
        
        data = userinfo_res.json()

        return ExternalOAuthProvider(
            provider=OAuthProvider.GOOGLE,
            provider_user_id=data["sub"],
            email=data["email"],
            phone="",
            first_name=data.get("given_name", ""),
            last_name=data.get("family_name", ""),
            avater_url=data.get("picture")
        )