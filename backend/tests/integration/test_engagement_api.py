"""Like/unlike and leaderboard/contribution API."""

import base64
import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm
from core.domain.value_objects import PostStatus

pytestmark = pytest.mark.django_db

PNG = base64.b64encode(
    base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
).decode()
PHOTO = f"data:image/png;base64,{PNG}"


def auth(client, username):
    client.post("/api/auth/register/", {
        "username": username, "email": f"{username}@e.com", "first_name": username,
        "last_name": "T", "phone": "+880", "password": "s3cretpass",
    }, format="json")
    code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
    client.post("/api/auth/verify/", {"username": username, "code": code}, format="json")
    return client.post("/api/auth/login/", {
        "username": username, "password": "s3cretpass"}, format="json").data["access"]


def approved_post(reporter_id=None):
    post = orm.Post.objects.create(
        reporter_name="R", reporter_email="r@e.com", reporter_phone="x",
        reporter_user_id=reporter_id, severity=3, image_provider="local",
        image_external_id="i", lat=23.8, lon=90.4, description="d",
        status=int(PostStatus.APPROVED), created="2026-07-18T12:00:00Z",
        approved_at="2026-07-18T12:00:00Z",
    )
    return post.id


class TestLike:
    def test_authenticated_user_likes(self):
        c = APIClient()
        access = auth(c, "bob")
        alice = orm.User.objects.create(username="alice", email="a@e.com", password="x")
        pid = approved_post(reporter_id=alice.id)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = c.post(f"/api/posts/{pid}/like/")
        assert resp.status_code == 201
        assert resp.data["likes"] == 1
        assert resp.data["liked_by_me"] is True

    def test_anonymous_can_like_but_liked_by_me_false(self):
        c = APIClient()
        pid = approved_post()
        resp = c.post(f"/api/posts/{pid}/like/")
        assert resp.status_code == 201
        assert resp.data["likes"] == 1
        assert resp.data["liked_by_me"] is False

    def test_double_like_conflicts(self):
        c = APIClient()
        access = auth(c, "bob")
        alice = orm.User.objects.create(username="alice", email="a@e.com", password="x")
        pid = approved_post(reporter_id=alice.id)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        c.post(f"/api/posts/{pid}/like/")
        assert c.post(f"/api/posts/{pid}/like/").status_code == 409

    def test_self_like_refused(self):
        c = APIClient()
        access = auth(c, "bob")
        bob = orm.User.objects.get(username="bob")
        pid = approved_post(reporter_id=bob.id)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        assert c.post(f"/api/posts/{pid}/like/").status_code == 409

    def test_cannot_like_pending_post(self):
        c = APIClient()
        pid = orm.Post.objects.create(
            reporter_name="R", reporter_email="r@e.com", reporter_phone="x",
            severity=3, image_provider="local", image_external_id="i",
            lat=23.8, lon=90.4, status=int(PostStatus.PENDING), created="2026-07-18T12:00:00Z",
        ).id
        assert c.post(f"/api/posts/{pid}/like/").status_code == 404

    def test_unlike(self):
        c = APIClient()
        access = auth(c, "bob")
        alice = orm.User.objects.create(username="alice", email="a@e.com", password="x")
        pid = approved_post(reporter_id=alice.id)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        c.post(f"/api/posts/{pid}/like/")
        resp = c.delete(f"/api/posts/{pid}/like/")
        assert resp.status_code == 200
        assert resp.data["likes"] == 0


class TestScoring:
    def test_leaderboard_is_public(self):
        assert APIClient().get("/api/leaderboard/").status_code == 200

    def test_leaderboard_reflects_points(self):
        c = APIClient()
        access = auth(c, "bob")
        alice = orm.User.objects.create(
            username="alice", email="a@e.com", password="x",
            first_name="Alice", last_name="T", date_joined="2026-07-18T12:00:00Z",
        )
        pid = approved_post(reporter_id=alice.id)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        c.post(f"/api/posts/{pid}/like/")

        board = APIClient().get("/api/leaderboard/").data["results"]
        by_user = {r["username"]: r["points"] for r in board}
        assert by_user["alice"] == 103  # post + like received
        assert by_user["bob"] == 1  # like given

    def test_contribution_requires_auth(self):
        assert APIClient().get("/api/me/contribution/").status_code == 401

    def test_contribution_returns_breakdown(self):
        c = APIClient()
        access = auth(c, "bob")
        bob = orm.User.objects.get(username="bob")
        approved_post(reporter_id=bob.id)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        data = c.get("/api/me/contribution/").data
        assert data["posts_approved"] == 1
        assert data["total_points"] == 100
        assert data["level"] >= 1
        assert "level_title" in data
