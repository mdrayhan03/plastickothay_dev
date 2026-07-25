"""Auth API - end-to-end through DRF, use cases, and the real ORM.

Exercises register → OTP → verify → login → refresh → logout and the security properties
around them (LLD §8.1). Email is captured by the locmem backend; the OTP is read out of it.
"""

import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def _register(client, username="alice"):
    return client.post(
        "/api/auth/register/",
        {
            "username": username,
            "email": f"{username}@example.com",
            "first_name": "Alice",
            "last_name": "Tester",
            "phone": "+8801700000000",
            "password": "s3cretpass",
        },
        format="json",
    )


def _otp_from_email() -> int:
    body = mail.outbox[-1].body
    return int(re.search(r"\b(\d{6})\b", body).group(1))


def _verify_and_login(client, username="alice"):
    _register(client, username)
    client.post(
        "/api/auth/verify/", {"username": username, "code": _otp_from_email()}, format="json"
    )
    resp = client.post(
        "/api/auth/login/", {"username": username, "password": "s3cretpass"}, format="json"
    )
    return resp


class TestRegistrationAndVerification:
    def test_register_creates_unverified_user_and_emails_otp(self, client):
        resp = _register(client)
        assert resp.status_code == 201
        user = orm.User.objects.get(username="alice")
        assert user.is_verified is False
        assert len(mail.outbox) == 1

    def test_duplicate_username_conflicts(self, client):
        _register(client)
        resp = _register(client)
        assert resp.status_code == 409
        assert resp.data["error"]["code"] == "username_taken"

    def test_verify_marks_user_verified(self, client):
        _register(client)
        resp = client.post(
            "/api/auth/verify/", {"username": "alice", "code": _otp_from_email()}, format="json"
        )
        assert resp.status_code == 200
        assert orm.User.objects.get(username="alice").is_verified is True

    def test_wrong_otp_rejected(self, client):
        _register(client)
        resp = client.post(
            "/api/auth/verify/", {"username": "alice", "code": 111111}, format="json"
        )
        assert resp.status_code == 400
        assert resp.data["error"]["code"] in ("otp_invalid", "otp_expired")


class TestLogin:
    def test_unverified_user_cannot_log_in(self, client):
        _register(client)
        resp = client.post(
            "/api/auth/login/", {"username": "alice", "password": "s3cretpass"}, format="json"
        )
        assert resp.status_code == 403
        assert resp.data["error"]["code"] == "account_not_verified"

    def test_wrong_password_is_400_not_403(self, client):
        """A wrong password must not reveal whether the account is verified/exists."""
        _register(client)
        client.post(
            "/api/auth/verify/", {"username": "alice", "code": _otp_from_email()}, format="json"
        )
        resp = client.post(
            "/api/auth/login/", {"username": "alice", "password": "wrong"}, format="json"
        )
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_credentials"

    def test_login_returns_access_in_body_and_refresh_in_httponly_cookie(self, client):
        resp = _verify_and_login(client)
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" not in resp.data  # refresh must NOT be in the body
        cookie = resp.cookies.get("refresh_token")
        assert cookie is not None
        assert cookie["httponly"] is True
        assert cookie["path"] == "/api/auth/"


class TestRefreshAndLogout:
    def test_refresh_rotates_and_issues_new_access(self, client):
        login = _verify_and_login(client)
        client.cookies["refresh_token"] = login.cookies["refresh_token"].value
        resp = client.post("/api/auth/refresh/", format="json")
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_refresh_without_cookie_fails(self, client):
        resp = client.post("/api/auth/refresh/", format="json")
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_token"

    def test_logout_revokes_refresh_token(self, client):
        login = _verify_and_login(client)
        refresh = login.cookies["refresh_token"].value
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        client.cookies["refresh_token"] = refresh
        out = client.post("/api/auth/logout/", format="json")
        assert out.status_code == 200

        # The revoked refresh token can no longer be rotated.
        fresh = APIClient()
        fresh.cookies["refresh_token"] = refresh
        resp = fresh.post("/api/auth/refresh/", format="json")
        assert resp.status_code == 400


class TestProtectedEndpoints:
    def test_me_requires_auth(self, client):
        assert client.get("/api/me/").status_code == 401

    def test_me_returns_profile_when_authenticated(self, client):
        login = _verify_and_login(client)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        resp = client.get("/api/me/")
        assert resp.status_code == 200
        assert resp.data["username"] == "alice"
        assert resp.data["role"] == "user"

    def test_anonymous_reaches_allowany_without_401(self, client):
        """The auth class returns None (not 401) with no token, so AllowAny is reachable.

        Register is AllowAny; hitting it with no Authorization header must not 401.
        """
        resp = _register(client, "anon_ok")
        assert resp.status_code == 201


PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
AVATAR = f"data:image/png;base64,{PNG}"


class TestAvatar:
    def _login_me(self, client, username="alice"):
        access = _verify_and_login(client, username).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_register_with_avatar_exposes_url_on_me(self, client):
        client.post(
            "/api/auth/register/",
            {
                "username": "alice",
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Tester",
                "phone": "+880170",
                "password": "s3cretpass",
                "avatar": AVATAR,
            },
            format="json",
        )
        client.post(
            "/api/auth/verify/", {"username": "alice", "code": _otp_from_email()}, format="json"
        )
        access = client.post(
            "/api/auth/login/", {"username": "alice", "password": "s3cretpass"}, format="json"
        ).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        me = client.get("/api/me/").data
        assert me["avatar_url"]
        assert orm.User.objects.get(username="alice").avatar_external_id != ""

    def test_no_avatar_is_null(self, client):
        self._login_me(client)
        assert client.get("/api/me/").data["avatar_url"] is None

    def test_update_profile_sets_avatar(self, client):
        self._login_me(client)
        resp = client.patch("/api/me/", {"avatar": AVATAR}, format="json")
        assert resp.status_code == 200
        assert resp.data["avatar_url"]

    def test_update_profile_without_avatar_keeps_existing(self, client):
        self._login_me(client)
        client.patch("/api/me/", {"avatar": AVATAR}, format="json")
        resp = client.patch("/api/me/", {"first_name": "Alicia"}, format="json")
        assert resp.data["first_name"] == "Alicia"
        assert resp.data["avatar_url"]  # not wiped


class TestPasswordReset:
    def test_reset_flow(self, client):
        _verify_and_login(client)
        client.post("/api/auth/forgot-password/", {"username": "alice"}, format="json")
        code = _otp_from_email()
        resp = client.post(
            "/api/auth/reset-password/",
            {"username": "alice", "code": code, "new_password": "newpass123"},
            format="json",
        )
        assert resp.status_code == 200

        login = client.post(
            "/api/auth/login/", {"username": "alice", "password": "newpass123"}, format="json"
        )
        assert login.status_code == 200
