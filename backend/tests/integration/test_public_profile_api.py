"""Public user profile + that user's approved reports (BE-10). World-readable, no PII."""

import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm
from core.domain.value_objects import PostStatus

pytestmark = pytest.mark.django_db

PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
PHOTO = f"data:image/png;base64,{PNG}"


def logged_in(username="alice"):
    c = APIClient()
    c.post(
        "/api/auth/register/",
        {
            "username": username,
            "email": f"{username}@example.com",
            "first_name": username.capitalize(),
            "last_name": "Tester",
            "phone": "+880170",
            "password": "s3cretpass",
        },
        format="json",
    )
    code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
    c.post("/api/auth/verify/", {"username": username, "code": code}, format="json")
    access = c.post(
        "/api/auth/login/", {"username": username, "password": "s3cretpass"}, format="json"
    ).data["access"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return c


def submit(client):
    return client.post(
        "/api/posts/", {"severity": 3, "lat": 23.8, "lon": 90.4, "photo": PHOTO}, format="json"
    ).data["id"]


def approve(pid):
    orm.Post.objects.filter(pk=pid).update(
        status=int(PostStatus.APPROVED), approved_at="2026-07-18T12:00:00Z"
    )


def uid(username="alice"):
    return orm.User.objects.get(username=username).id


def insert_approved(user_id, n):
    """Create approved posts directly, bypassing the submission throttle."""
    for i in range(n):
        orm.Post.objects.create(
            reporter_name="Alice",
            reporter_email="a@e.com",
            reporter_phone="+880",
            reporter_user_id=user_id,
            severity=3,
            image_provider="fake",
            image_external_id=f"img-{i}",
            lat=23.8,
            lon=90.4,
            description="d",
            status=int(PostStatus.APPROVED),
            created="2026-07-18T12:00:00Z",
            approved_at="2026-07-18T12:00:00Z",
        )


class TestPublicProfile:
    def test_is_public_and_privacy_limited(self):
        author = logged_in("alice")
        approve(submit(author))

        res = APIClient().get(f"/api/users/{uid()}/")  # anonymous viewer
        assert res.status_code == 200
        data = res.data
        assert data["username"] == "alice"
        assert data["full_name"] == "Alice Tester"
        assert data["posts_approved"] == 1
        for leaked in ("email", "phone", "reporter_email"):
            assert leaked not in data
        assert "level" in data and "badges" in data and "avatar_url" in data

    def test_unknown_user_404(self):
        assert APIClient().get("/api/users/99999/").status_code == 404

    def test_inactive_user_404(self):
        logged_in("alice")
        orm.User.objects.filter(username="alice").update(is_active=False)
        assert APIClient().get(f"/api/users/{uid()}/").status_code == 404


class TestUserPosts:
    def test_returns_only_approved_reports(self):
        author = logged_in("alice")
        approved = submit(author)
        approve(approved)
        submit(author)  # left pending

        results = APIClient().get(f"/api/users/{uid()}/posts/").data["results"]
        ids = {p["id"] for p in results}
        assert approved in ids
        assert len(ids) == 1  # the pending one is not public

    def test_paginates_at_five(self):
        logged_in("alice")
        insert_approved(uid(), 6)
        page = APIClient().get(f"/api/users/{uid()}/posts/").data
        assert len(page["results"]) == 5
        assert page["next_cursor"] is not None

    def test_excludes_other_users_reports(self):
        alice = logged_in("alice")
        approve(submit(alice))
        bob = logged_in("bob")
        approve(submit(bob))
        results = APIClient().get(f"/api/users/{uid('bob')}/posts/").data["results"]
        assert all(p["reporter_id"] == uid("bob") for p in results)
        assert len(results) == 1
