"""Reports API — submission, public reads, and the PII guarantee.

The PII regression test is the point of this milestone: reporter email/phone must never appear
in any public response (LLD §8.3).
"""

import base64

import pytest
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm
from core.domain.value_objects import PostStatus

pytestmark = pytest.mark.django_db

# 1x1 transparent PNG.
PNG = base64.b64encode(
    base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
).decode()
PHOTO = f"data:image/png;base64,{PNG}"


@pytest.fixture
def client():
    return APIClient()


def submit(client, **over):
    payload = {
        "severity": 3, "lat": 23.8103, "lon": 90.4125, "photo": PHOTO,
        "description": "Plastic near the canal.",
        "name": "Walk-in", "email": "walkin@example.com", "phone": "+8801799999999",
    }
    payload.update(over)
    return client.post("/api/posts/", payload, format="json")


def approve(post_id):
    orm.Post.objects.filter(pk=post_id).update(
        status=int(PostStatus.APPROVED), approved_at="2026-07-18T12:00:00Z"
    )


class TestSubmission:
    def test_anonymous_can_submit(self, client):
        resp = submit(client)
        assert resp.status_code == 201
        post = orm.Post.objects.get(pk=resp.data["id"])
        assert post.status == int(PostStatus.PENDING)
        assert post.reporter_user_id is None
        assert post.reporter_email == "walkin@example.com"

    def test_invalid_base64_rejected(self, client):
        resp = submit(client, photo="data:image/png;base64,@@@notbase64@@@")
        assert resp.status_code == 400

    def test_out_of_range_severity_rejected(self, client):
        assert submit(client, severity=9).status_code == 400

    def test_submitted_post_is_not_public_until_approved(self, client):
        submit(client)
        assert client.get("/api/posts/").data["results"] == []


class TestPublicReads:
    def test_list_returns_only_approved(self, client):
        pending = submit(client).data["id"]
        approved = submit(client).data["id"]
        approve(approved)

        ids = [p["id"] for p in client.get("/api/posts/").data["results"]]
        assert approved in ids
        assert pending not in ids

    def test_detail_of_pending_is_404_not_403(self, client):
        """404, not 403 — a 403 would confirm the post exists and leak the queue."""
        pid = submit(client).data["id"]
        assert client.get(f"/api/posts/{pid}/").status_code == 404

    def test_map_returns_approved_markers_only(self, client):
        submit(client)  # pending
        approved = submit(client).data["id"]
        approve(approved)
        markers = client.get("/api/map/posts/").data
        assert len(markers) == 1
        assert markers[0]["id"] == approved
        assert set(markers[0].keys()) == {"id", "lat", "lon", "severity"}


class TestPIIneverLeaks:
    def test_public_list_has_no_email_or_phone(self, client):
        approve(submit(client).data["id"])
        row = client.get("/api/posts/").data["results"][0]
        assert "reporter_email" not in row
        assert "reporter_phone" not in row
        assert "email" not in row
        assert "phone" not in row
        assert row["reporter_name"] == "Walk-in"  # name is fine

    def test_public_detail_has_no_email_or_phone(self, client):
        pid = submit(client).data["id"]
        approve(pid)
        row = client.get(f"/api/posts/{pid}/").data
        assert "reporter_email" not in row and "reporter_phone" not in row

    def test_raw_response_body_never_contains_the_email(self, client):
        """Belt and braces: scan the serialized bytes for the address itself."""
        approve(submit(client, email="secret@victim.com").data["id"])
        body = client.get("/api/posts/").content.decode()
        assert "secret@victim.com" not in body
        assert "+8801799999999" not in body


class TestAuthenticatedSubmission:
    def _auth(self, client):
        import re

        from django.core import mail

        client.post("/api/auth/register/", {
            "username": "bob", "email": "bob@example.com", "first_name": "Bob",
            "last_name": "T", "phone": "+8801700000000", "password": "s3cretpass",
        }, format="json")
        code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
        client.post("/api/auth/verify/", {"username": "bob", "code": code}, format="json")
        access = client.post("/api/auth/login/", {
            "username": "bob", "password": "s3cretpass"}, format="json").data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_authenticated_submit_ignores_body_contact_details(self, client):
        self._auth(client)
        pid = submit(client, name="Someone Else", email="victim@example.com").data["id"]
        post = orm.Post.objects.get(pk=pid)
        assert post.reporter_user_id is not None
        assert post.reporter_email == "bob@example.com"  # profile, not the body
