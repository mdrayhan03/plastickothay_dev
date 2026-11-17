"""OAuth API - end-to-end through DRF, use cases, and the real ORM."""

import pytest
import requests
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm

pytestmark = pytest.mark.django_db

OAUTH_GOOGLE_URL = "/api/auth/oauth/google"
CALLBACK_URI = "http://localhost:5173/oauth/callback"


@pytest.fixture
def client():
    return APIClient()


class FakeHttpResponse:
    def __init__(self, status_code: int = 200, json_data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._json = json_data or {}
        self.text = text or str(self._json)

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _patch_google(
    monkeypatch,
    *,
    sub: str = "100200300400",
    email: str = "alice@example.com",
    given_name: str = "Alice",
    family_name: str = "Tester",
    picture: str | None = "https://lh3.googleusercontent.com/a/alice=s96-c",
    phone: str = "+8801700000000",
    token_status: int = 200,
):
    def fake_post(url, *args, **kwargs):
        if token_status != 200:
            return FakeHttpResponse(token_status, {"error": "invalid_grant"})
        return FakeHttpResponse(200, {"access_token": "mock-google-access-token"})

    def fake_get(url, *args, **kwargs):
        if "people.googleapis.com" in url:
            return FakeHttpResponse(
                200,
                {
                    "resourceName": f"people/{sub}",
                    "emailAddresses": [{"value": email, "metadata": {"primary": True}}],
                    "names": [
                        {
                            "givenName": given_name,
                            "familyName": family_name,
                            "metadata": {"primary": True},
                        }
                    ],
                    "photos": [{"url": picture, "metadata": {"primary": True}}] if picture else [],
                    "phoneNumbers": (
                        [{"canonicalForm": phone, "metadata": {"primary": True}}] if phone else []
                    ),
                },
            )

        userinfo = {
            "sub": sub,
            "email": email,
            "given_name": given_name,
            "family_name": family_name,
        }
        if picture:
            userinfo["picture"] = picture
        return FakeHttpResponse(200, userinfo)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)


def _oauth_login(client, code: str = "valid-google-code"):
    return client.post(
        OAUTH_GOOGLE_URL,
        {"code": code, "redirect_uri": CALLBACK_URI},
        format="json",
    )


class TestGoogleOAuth:
    def test_new_user_signup_creates_verified_user_and_social_identity(self, client, monkeypatch):
        _patch_google(
            monkeypatch,
            sub="100200300",
            email="alice@example.com",
            given_name="Alice",
            family_name="Tester",
            picture="https://lh3.googleusercontent.com/a/alice=s96-c",
            phone="+8801700000000",
        )

        resp = _oauth_login(client)
        assert resp.status_code == 200

        user = orm.User.objects.get(email="alice@example.com")
        assert user.is_verified is True
        assert user.first_name == "Alice"
        assert user.last_name == "Tester"
        assert user.phone == ""
        assert user.avatar_external_id == "https://lh3.googleusercontent.com/a/alice=s96-c"

        identity = orm.SocialIdentity.objects.get(provider="google", provider_user_id="100200300")
        assert identity.user_id == user.id

    def test_returns_access_in_body_and_refresh_in_httponly_cookie(self, client, monkeypatch):
        _patch_google(monkeypatch)

        resp = _oauth_login(client)
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" not in resp.data
        cookie = resp.cookies.get("refresh_token")
        assert cookie is not None
        assert cookie["httponly"] is True
        assert cookie["path"] == "/api/auth/"

    def test_returning_social_user_reuses_existing_account(self, client, monkeypatch):
        _patch_google(monkeypatch, sub="sub-returning-1", email="alice@example.com")

        first = _oauth_login(client, code="code-1")
        second = _oauth_login(client, code="code-2")

        assert first.status_code == 200
        assert second.status_code == 200
        assert orm.User.objects.filter(email="alice@example.com").count() == 1
        assert (
            orm.SocialIdentity.objects.filter(
                provider="google", provider_user_id="sub-returning-1"
            ).count()
            == 1
        )

    def test_links_google_to_existing_email_user(self, client, monkeypatch):
        existing = orm.User.objects.create_user(
            username="alice_local",
            email="alice@example.com",
            password="s3cretpass",
            is_verified=False,
        )
        _patch_google(monkeypatch, sub="sub-linked-1", email="alice@example.com")

        resp = _oauth_login(client)
        assert resp.status_code == 200
        assert orm.User.objects.filter(email="alice@example.com").count() == 1
        assert orm.SocialIdentity.objects.filter(
            user=existing, provider="google", provider_user_id="sub-linked-1"
        ).exists()

    def test_missing_phone_and_avatar_still_succeeds(self, client, monkeypatch):
        _patch_google(
            monkeypatch,
            sub="sub-minimal-1",
            email="minimal@example.com",
            picture=None,
            phone="",
        )

        resp = _oauth_login(client)
        assert resp.status_code == 200
        user = orm.User.objects.get(email="minimal@example.com")
        assert user.phone == ""

    def test_oauth_tokens_work_with_me_and_refresh(self, client, monkeypatch):
        _patch_google(monkeypatch, sub="sub-session-1", email="session@example.com")

        login = _oauth_login(client)
        access = login.data["access"]
        refresh = login.cookies["refresh_token"].value

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me = client.get("/api/me/")
        assert me.status_code == 200
        assert me.data["email"] == "session@example.com"
        assert me.data["avatar_url"]

        client.cookies["refresh_token"] = refresh
        refreshed = client.post("/api/auth/refresh/", format="json")
        assert refreshed.status_code == 200
        assert "access" in refreshed.data

    def test_inactive_user_rejected(self, client, monkeypatch):
        banned = orm.User.objects.create_user(
            username="banned_alice", email="banned@example.com", is_active=False
        )
        orm.SocialIdentity.objects.create(
            user=banned,
            provider="google",
            provider_user_id="sub-banned-1",
            created=banned.date_joined,
        )
        _patch_google(monkeypatch, sub="sub-banned-1", email="banned@example.com")

        resp = _oauth_login(client)
        assert resp.status_code in (400, 403)
        assert "error" in resp.data
        assert "refresh_token" not in resp.cookies

    def test_invalid_google_code_returns_error_envelope(self, client, monkeypatch):
        _patch_google(monkeypatch, token_status=400)

        resp = _oauth_login(client, code="bad-code")
        assert resp.status_code in (400, 502)
        assert "error" in resp.data
        assert resp.data["error"]["code"]
        assert orm.User.objects.count() == 0

    def test_missing_code_or_redirect_uri_returns_400(self, client):
        resp = client.post(OAUTH_GOOGLE_URL, {"code": "only-code"}, format="json")
        assert resp.status_code == 400
        assert "error" in resp.data