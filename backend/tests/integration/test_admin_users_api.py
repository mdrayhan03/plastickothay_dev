"""Admin users API (BE-0) - list, activate/deactivate (staff), role change (admin)."""

import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm
from core.domain.value_objects import Role

pytestmark = pytest.mark.django_db


def make_verified_user(client, username, role=Role.USER):
    client.post(
        "/api/auth/register/",
        {
            "username": username,
            "email": f"{username}@example.com",
            "first_name": username,
            "last_name": "T",
            "phone": "+880170",
            "password": "s3cretpass",
        },
        format="json",
    )
    code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
    client.post("/api/auth/verify/", {"username": username, "code": code}, format="json")
    if role is not Role.USER:
        u = orm.User.objects.get(username=username)
        u.is_superuser = role is Role.ADMIN
        u.is_staff = role in (Role.STAFF, Role.ADMIN)
        u.save()
    access = client.post(
        "/api/auth/login/", {"username": username, "password": "s3cretpass"}, format="json"
    ).data["access"]
    return access


def client_for(username, role=Role.USER):
    c = APIClient()
    access = make_verified_user(c, username, role=role)
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return c


def uid(username):
    return orm.User.objects.get(username=username).id


class TestList:
    def test_anonymous_gets_401(self):
        assert APIClient().get("/api/admin/users/").status_code == 401

    def test_regular_user_gets_403(self):
        assert client_for("alice").get("/api/admin/users/").status_code == 403

    def test_staff_sees_the_list(self):
        c = client_for("mod", role=Role.STAFF)
        make_verified_user(APIClient(), "alice")
        res = c.get("/api/admin/users/")
        assert res.status_code == 200
        assert "results" in res.data and "next_cursor" in res.data
        usernames = {u["username"] for u in res.data["results"]}
        assert {"mod", "alice"} <= usernames
        row = next(u for u in res.data["results"] if u["username"] == "alice")
        assert row["role"] == "user" and row["is_active"] is True
        assert "password" not in row


class TestDetail:
    def test_staff_sees_user_with_stats(self):
        c = client_for("mod", role=Role.STAFF)
        make_verified_user(APIClient(), "alice")
        res = c.get(f"/api/admin/users/{uid('alice')}/")
        assert res.status_code == 200
        assert res.data["username"] == "alice"
        for k in ("posts_approved", "likes_received", "total_points"):
            assert isinstance(res.data[k], int)

    def test_regular_user_gets_403(self):
        c = client_for("alice")
        make_verified_user(APIClient(), "bob")
        assert c.get(f"/api/admin/users/{uid('bob')}/").status_code == 403

    def test_unknown_user_404(self):
        c = client_for("mod", role=Role.STAFF)
        assert c.get("/api/admin/users/99999/").status_code == 404


class TestActivate:
    def test_staff_can_deactivate_a_user(self):
        c = client_for("mod", role=Role.STAFF)
        make_verified_user(APIClient(), "alice")
        res = c.patch(
            f"/api/admin/users/{uid('alice')}/active/", {"is_active": False}, format="json"
        )
        assert res.status_code == 200
        assert res.data["is_active"] is False
        assert orm.User.objects.get(username="alice").is_active is False

    def test_staff_cannot_deactivate_an_admin(self):
        c = client_for("mod", role=Role.STAFF)
        make_verified_user(APIClient(), "boss", role=Role.ADMIN)
        res = c.patch(
            f"/api/admin/users/{uid('boss')}/active/", {"is_active": False}, format="json"
        )
        assert res.status_code == 403

    def test_cannot_deactivate_self(self):
        c = client_for("mod", role=Role.STAFF)
        res = c.patch(f"/api/admin/users/{uid('mod')}/active/", {"is_active": False}, format="json")
        assert res.status_code == 403

    def test_regular_user_gets_403(self):
        c = client_for("alice")
        make_verified_user(APIClient(), "bob")
        res = c.patch(f"/api/admin/users/{uid('bob')}/active/", {"is_active": False}, format="json")
        assert res.status_code == 403


class TestRole:
    def test_admin_can_change_role(self):
        c = client_for("boss", role=Role.ADMIN)
        make_verified_user(APIClient(), "alice")
        res = c.patch(f"/api/admin/users/{uid('alice')}/role/", {"role": "staff"}, format="json")
        assert res.status_code == 200
        assert res.data["role"] == "staff"
        u = orm.User.objects.get(username="alice")
        assert u.is_staff is True and u.is_superuser is False

    def test_staff_cannot_change_role(self):
        c = client_for("mod", role=Role.STAFF)
        make_verified_user(APIClient(), "alice")
        res = c.patch(f"/api/admin/users/{uid('alice')}/role/", {"role": "staff"}, format="json")
        assert res.status_code == 403

    def test_cannot_change_own_role(self):
        c = client_for("boss", role=Role.ADMIN)
        res = c.patch(f"/api/admin/users/{uid('boss')}/role/", {"role": "user"}, format="json")
        assert res.status_code == 403

    def test_invalid_role_is_400(self):
        c = client_for("boss", role=Role.ADMIN)
        make_verified_user(APIClient(), "alice")
        res = c.patch(f"/api/admin/users/{uid('alice')}/role/", {"role": "wizard"}, format="json")
        assert res.status_code == 400


class TestDelete:
    def _deactivate(self, username):
        u = orm.User.objects.get(username=username)
        u.is_active = False
        u.save()

    def test_admin_deletes_an_inactive_user(self):
        c = client_for("boss", role=Role.ADMIN)
        make_verified_user(APIClient(), "alice")
        self._deactivate("alice")
        target = uid("alice")
        res = c.delete(f"/api/admin/users/{target}/")
        assert res.status_code == 204
        assert not orm.User.objects.filter(pk=target).exists()

    def test_cannot_delete_an_active_user(self):
        c = client_for("boss", role=Role.ADMIN)
        make_verified_user(APIClient(), "alice")
        res = c.delete(f"/api/admin/users/{uid('alice')}/")
        assert res.status_code == 409

    def test_staff_cannot_delete(self):
        c = client_for("mod", role=Role.STAFF)
        make_verified_user(APIClient(), "alice")
        self._deactivate("alice")
        res = c.delete(f"/api/admin/users/{uid('alice')}/")
        assert res.status_code == 403

    def test_cannot_delete_self(self):
        c = client_for("boss", role=Role.ADMIN)
        res = c.delete(f"/api/admin/users/{uid('boss')}/")
        assert res.status_code == 403

    def test_deleting_a_user_keeps_their_reports_anonymised(self):
        c = client_for("boss", role=Role.ADMIN)
        reporter = client_for("alice")
        png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        pid = reporter.post(
            "/api/posts/",
            {
                "severity": 3,
                "lat": 23.8,
                "lon": 90.4,
                "photo": f"data:image/png;base64,{png}",
            },
            format="json",
        ).data["id"]
        self._deactivate("alice")
        c.delete(f"/api/admin/users/{uid('alice')}/")
        post = orm.Post.objects.get(pk=pid)
        assert post.reporter_user_id is None
