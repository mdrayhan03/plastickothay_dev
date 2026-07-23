"""Moderation API — admin-only approve/reject/hide/unhide and stats."""

import base64
import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm
from core.domain.value_objects import PostStatus, Role

pytestmark = pytest.mark.django_db

PNG = base64.b64encode(
    base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
).decode()
PHOTO = f"data:image/png;base64,{PNG}"


def make_verified_user(client, username, role=Role.USER):
    client.post("/api/auth/register/", {
        "username": username, "email": f"{username}@example.com", "first_name": username,
        "last_name": "T", "phone": "+880170", "password": "s3cretpass",
    }, format="json")
    code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
    client.post("/api/auth/verify/", {"username": username, "code": code}, format="json")
    if role is not Role.USER:
        u = orm.User.objects.get(username=username)
        u.is_superuser = role is Role.ADMIN
        u.is_staff = role in (Role.STAFF, Role.ADMIN)
        u.save()
    access = client.post("/api/auth/login/", {
        "username": username, "password": "s3cretpass"}, format="json").data["access"]
    return access


def submit(client):
    return client.post("/api/posts/", {
        "severity": 3, "lat": 23.8, "lon": 90.4, "photo": PHOTO,
        "name": "Anon", "email": "anon@example.com", "phone": "+880111",
    }, format="json").data["id"]


@pytest.fixture
def admin_client():
    c = APIClient()
    access = make_verified_user(c, "boss", role=Role.ADMIN)
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return c


class TestPermissions:
    def test_anonymous_gets_401(self):
        c = APIClient()
        pid = submit(c)
        assert c.post(f"/api/admin/posts/{pid}/approve/").status_code == 401

    def test_regular_user_gets_403(self):
        c = APIClient()
        access = make_verified_user(c, "alice", role=Role.USER)
        pid = submit(c)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        assert c.post(f"/api/admin/posts/{pid}/approve/").status_code == 403

    def test_staff_can_moderate(self):
        c = APIClient()
        access = make_verified_user(c, "mod", role=Role.STAFF)
        pid = submit(c)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        assert c.post(f"/api/admin/posts/{pid}/approve/").status_code == 200


class TestApprove:
    def test_approve_makes_public_and_emails(self, admin_client):
        pid = submit(admin_client)
        mail.outbox.clear()
        resp = admin_client.post(f"/api/admin/posts/{pid}/approve/")
        assert resp.status_code == 200
        assert resp.data["status"] == int(PostStatus.APPROVED)
        assert orm.Post.objects.get(pk=pid).approved_at is not None
        assert len(mail.outbox) == 1  # reporter notified

    def test_admin_serializer_exposes_pii(self, admin_client):
        """The admin view is the ONE place email/phone are visible.

        Submit anonymously (a fresh client with no token) so the reporter details come from
        the body, not an authenticated profile.
        """
        pid = submit(APIClient())
        resp = admin_client.post(f"/api/admin/posts/{pid}/approve/")
        assert resp.data["reporter_email"] == "anon@example.com"
        assert "reporter_phone" in resp.data

    def test_double_approve_conflicts(self, admin_client):
        pid = submit(admin_client)
        admin_client.post(f"/api/admin/posts/{pid}/approve/")
        assert admin_client.post(f"/api/admin/posts/{pid}/approve/").status_code == 409


class TestRejectHideUnhide:
    def test_reject_soft_deletes(self, admin_client):
        pid = submit(admin_client)
        resp = admin_client.post(
            f"/api/admin/posts/{pid}/reject/", {"reason": "spam"}, format="json"
        )
        assert resp.status_code == 200
        row = orm.Post.objects.get(pk=pid)
        assert row.status == int(PostStatus.REJECTED)
        assert row.deleted_at is not None

    def test_hide_then_unhide_preserves_approved_at(self, admin_client):
        pid = submit(admin_client)
        admin_client.post(f"/api/admin/posts/{pid}/approve/")
        original = orm.Post.objects.get(pk=pid).approved_at

        admin_client.post(f"/api/admin/posts/{pid}/hide/")
        assert orm.Post.objects.get(pk=pid).status == int(PostStatus.HIDDEN)

        admin_client.post(f"/api/admin/posts/{pid}/unhide/")
        row = orm.Post.objects.get(pk=pid)
        assert row.status == int(PostStatus.APPROVED)
        assert row.approved_at == original  # not reset — would shift the leaderboard week

    def test_hide_requires_approved(self, admin_client):
        pid = submit(admin_client)  # pending
        assert admin_client.post(f"/api/admin/posts/{pid}/hide/").status_code == 409


class TestReviewListAndStats:
    def test_review_list_defaults_to_pending(self, admin_client):
        submit(admin_client)
        approved = submit(admin_client)
        admin_client.post(f"/api/admin/posts/{approved}/approve/")
        results = admin_client.get("/api/admin/posts/").data["results"]
        assert all(r["status"] == int(PostStatus.PENDING) for r in results)
        assert len(results) == 1

    def test_stats_counts_by_status(self, admin_client):
        p1 = submit(admin_client)
        submit(admin_client)
        admin_client.post(f"/api/admin/posts/{p1}/approve/")
        stats = admin_client.get("/api/admin/stats/").data
        assert stats["approved"] == 1
        assert stats["pending"] == 1
