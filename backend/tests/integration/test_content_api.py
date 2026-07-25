"""Content API — contact page, messages, feedback — and the Django-admin restriction."""

import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm

pytestmark = pytest.mark.django_db


def admin_access(client):
    client.post(
        "/api/auth/register/",
        {
            "username": "boss",
            "email": "boss@e.com",
            "first_name": "B",
            "last_name": "T",
            "phone": "+880",
            "password": "s3cretpass",
        },
        format="json",
    )
    code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
    client.post("/api/auth/verify/", {"username": "boss", "code": code}, format="json")
    u = orm.User.objects.get(username="boss")
    u.is_superuser = u.is_staff = True
    u.save()
    return client.post(
        "/api/auth/login/", {"username": "boss", "password": "s3cretpass"}, format="json"
    ).data["access"]


class TestContactPage:
    def test_publicly_readable(self):
        assert APIClient().get("/api/contact-page/").status_code == 200

    def test_only_admin_can_edit(self):
        assert APIClient().put("/api/contact-page/", {}, format="json").status_code == 401

    def test_admin_updates_page(self):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access(c)}")
        resp = c.put(
            "/api/contact-page/",
            {
                "heading": "Reach us",
                "intro": "Hi",
                "email": "hello@pk.org",
                "phone": "+8801",
                "address": "Dhaka",
                "socials": [{"platform": "fb", "url": "https://fb.com/pk", "order": 1}],
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["heading"] == "Reach us"
        assert resp.data["socials"][0]["platform"] == "fb"
        # Persisted and publicly visible.
        assert APIClient().get("/api/contact-page/").data["heading"] == "Reach us"


class TestContactMessages:
    def test_anonymous_can_submit(self):
        resp = APIClient().post(
            "/api/contact-messages/",
            {
                "subject": "Question",
                "message": "Hello",
                "name": "Sam",
                "email": "sam@e.com",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert orm.ContactMessage.objects.count() == 1

    def test_only_admin_lists_messages(self):
        APIClient().post(
            "/api/contact-messages/",
            {"subject": "Q", "message": "hi", "name": "Sam", "email": "sam@e.com"},
            format="json",
        )
        assert APIClient().get("/api/contact-messages/").status_code == 401

        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access(c)}")
        assert len(c.get("/api/contact-messages/").data["results"]) == 1

    def test_admin_updates_message_status(self):
        mid = (
            APIClient().post(
                "/api/contact-messages/",
                {"subject": "Q", "message": "hi", "name": "S", "email": "s@e.com"},
                format="json",
            )
            and orm.ContactMessage.objects.first().id
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access(c)}")
        resp = c.patch(f"/api/contact-messages/{mid}/", {"status": "read"}, format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == "read"


class TestFeedback:
    def test_anonymous_can_submit(self):
        resp = APIClient().post(
            "/api/feedback/", {"rating": 5, "comment": "Great", "name": "Sam"}, format="json"
        )
        assert resp.status_code == 201

    def test_rating_out_of_range_rejected(self):
        assert APIClient().post("/api/feedback/", {"rating": 9}, format="json").status_code == 400

    def test_not_public(self):
        """Feedback is never displayed publicly — GET requires admin."""
        assert APIClient().get("/api/feedback/").status_code == 401

    def test_admin_lists_feedback(self):
        APIClient().post("/api/feedback/", {"rating": 4, "comment": "ok"}, format="json")
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access(c)}")
        assert len(c.get("/api/feedback/").data["results"]) == 1


class TestDjangoAdminRestriction:
    """The rule from LLD §11.4: admin may touch config tables only."""

    def test_config_tables_are_registered(self):
        from django.contrib import admin

        registered = {m.__name__ for m in admin.site._registry}
        assert {"PointRule", "LevelRule", "ContactPage"} <= registered

    def test_post_is_never_registered_in_django_admin(self):
        from django.contrib import admin

        registered = {m.__name__ for m in admin.site._registry}
        # Post approval has behaviour that must go through use cases, never the admin.
        assert "Post" not in registered
        assert "Engagement" not in registered
