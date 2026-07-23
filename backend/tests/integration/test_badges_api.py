"""Badge API — award-on-read, idempotency, permanence."""

import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm
from core.domain.value_objects import PostStatus

pytestmark = pytest.mark.django_db


def auth(client, username="bob"):
    client.post("/api/auth/register/", {
        "username": username, "email": f"{username}@e.com", "first_name": username,
        "last_name": "T", "phone": "+880", "password": "s3cretpass",
    }, format="json")
    code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
    client.post("/api/auth/verify/", {"username": username, "code": code}, format="json")
    return client.post("/api/auth/login/", {
        "username": username, "password": "s3cretpass"}, format="json").data["access"]


def approved_post(reporter_id):
    orm.Post.objects.create(
        reporter_name="R", reporter_email="r@e.com", reporter_phone="x",
        reporter_user_id=reporter_id, severity=3, image_provider="local", image_external_id="i",
        lat=23.8, lon=90.4, status=int(PostStatus.APPROVED),
        created="2026-07-23T12:00:00Z", approved_at="2026-07-23T12:00:00Z",
    )


class TestBadges:
    def test_requires_auth(self):
        assert APIClient().get("/api/me/badges/").status_code == 401

    def test_no_badges_when_nothing_earned(self):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {auth(c)}")
        assert c.get("/api/me/badges/").data == []

    def test_first_report_badge_awarded_on_read(self):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {auth(c)}")
        approved_post(orm.User.objects.get(username="bob").id)

        data = c.get("/api/me/badges/").data
        codes = {b["code"] for b in data}
        assert "first_report" in codes
        assert data[0]["icon"] == "🌱"

    def test_award_is_persisted_and_idempotent(self):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {auth(c)}")
        bob = orm.User.objects.get(username="bob")
        approved_post(bob.id)

        c.get("/api/me/badges/")
        c.get("/api/me/badges/")  # second read must not double-award
        assert orm.UserBadge.objects.filter(user_id=bob.id, badge_code="first_report").count() == 1

    def test_badge_is_permanent_after_stat_drops(self):
        """Earned badges stay even if the underlying stat later drops (post hidden)."""
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {auth(c)}")
        bob = orm.User.objects.get(username="bob")
        approved_post(bob.id)
        c.get("/api/me/badges/")  # earns first_report

        orm.Post.objects.filter(reporter_user_id=bob.id).update(status=int(PostStatus.HIDDEN))

        codes = {b["code"] for b in c.get("/api/me/badges/").data}
        assert "first_report" in codes  # kept, though posts_approved is now 0

    def test_badge_rule_registered_in_django_admin_only(self):
        from django.contrib import admin

        registered = {m.__name__ for m in admin.site._registry}
        assert "BadgeRule" in registered      # config table — editable
        assert "UserBadge" not in registered  # earned records — not hand-edited
