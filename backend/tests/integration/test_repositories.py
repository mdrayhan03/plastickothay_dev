"""Repository integration tests — real ORM, real database.

Runs against whatever DATABASE_URL points at (SQLite locally, Postgres in CI). The mapper
round-trip and the DB-level constraints are what these prove; the behaviour above the
repository is already covered by the unit suite on fakes.

Concurrency (two simultaneous likes racing the partial unique index) needs real Postgres and
is deferred to B5 — SQLite serialises writers and cannot reproduce the race.
"""

from datetime import UTC, datetime

import pytest

from adapters.persistence.django_orm.repositories import (
    DjangoEngagementRepository,
    DjangoOTPRepository,
    DjangoPostRepository,
    DjangoUserRepository,
)
from core.domain.entities import OTP, Engagement, Post, User
from core.domain.errors import AlreadyLiked, EmailTaken, UsernameTaken
from core.domain.pagination import PageRequest
from core.domain.read_models import PostFilter
from core.domain.value_objects import (
    EngagementType,
    GeoPoint,
    ImageRef,
    OTPPurpose,
    PostStatus,
    Reporter,
    Role,
    Severity,
)

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def make_user(username="alice", role=Role.USER):
    return DjangoUserRepository().add(
        User(
            id=None,
            username=username,
            email=f"{username}@example.com",
            first_name=username.capitalize(),
            last_name="Tester",
            phone="+8801700000000",
            role=role,
            is_verified=True,
            is_active=True,
            date_joined=NOW,
        ),
        password="secret123",
    )


def make_post(reporter_id=None, status=PostStatus.APPROVED):
    return DjangoPostRepository().add(
        Post(
            id=None,
            reporter=Reporter("Anon", "anon@example.com", "+8801711111111"),
            reporter_id=reporter_id,
            severity=Severity.MODERATE,
            image=ImageRef("gdrive", "img-1"),
            location=GeoPoint(23.8103, 90.4125),
            description="Plastic pile.",
            status=status,
            created=NOW,
            approved_at=NOW if status is PostStatus.APPROVED else None,
        )
    )


class TestUserRepository:
    def test_round_trips_through_the_mapper(self):
        created = make_user("alice", role=Role.STAFF)
        fetched = DjangoUserRepository().get(created.id)

        assert fetched.username == "alice"
        assert fetched.email == "alice@example.com"
        assert fetched.role is Role.STAFF  # derived from is_staff flag
        assert fetched.is_verified is True

    def test_role_admin_maps_to_superuser(self):
        created = make_user("boss", role=Role.ADMIN)
        assert DjangoUserRepository().get(created.id).role is Role.ADMIN

    def test_duplicate_username_raises(self):
        make_user("alice")
        with pytest.raises((UsernameTaken, EmailTaken)):
            DjangoUserRepository().add(
                User(
                    id=None, username="alice", email="other@example.com",
                    first_name="A", last_name="B", phone="x", role=Role.USER,
                    is_verified=False, is_active=True, date_joined=NOW,
                ),
                password="secret123",
            )

    def test_duplicate_email_raises(self):
        make_user("alice")
        with pytest.raises((EmailTaken, UsernameTaken)):
            DjangoUserRepository().add(
                User(
                    id=None, username="bob", email="alice@example.com",
                    first_name="A", last_name="B", phone="x", role=Role.USER,
                    is_verified=False, is_active=True, date_joined=NOW,
                ),
                password="secret123",
            )

    def test_password_hashed_and_verifiable(self):
        user = make_user("alice")
        repo = DjangoUserRepository()
        assert repo.verify_password(user.id, "secret123") is True
        assert repo.verify_password(user.id, "wrong") is False


class TestOTPRepository:
    def test_latest_valid_ignores_expired(self):
        repo = DjangoOTPRepository()
        repo.add(OTP(None, "alice", 111111, OTPPurpose.REGISTRATION, NOW,
                     datetime(2020, 1, 1, tzinfo=UTC)))  # expired
        repo.add(OTP(None, "alice", 222222, OTPPurpose.REGISTRATION, NOW,
                     datetime(2030, 1, 1, tzinfo=UTC)))  # valid

        found = repo.latest_valid_for("alice", OTPPurpose.REGISTRATION, NOW)
        assert found.code == 222222

    def test_purge_expired(self):
        repo = DjangoOTPRepository()
        repo.add(OTP(None, "alice", 111111, OTPPurpose.REGISTRATION, NOW,
                     datetime(2020, 1, 1, tzinfo=UTC)))
        assert repo.purge_expired(NOW) == 1


class TestPostRepository:
    def test_round_trips(self):
        created = make_post(status=PostStatus.PENDING)
        fetched = DjangoPostRepository().get(created.id)
        assert fetched.severity is Severity.MODERATE
        assert fetched.status is PostStatus.PENDING
        assert fetched.location.lat == 23.8103

    def test_list_filters_by_status(self):
        make_post(status=PostStatus.APPROVED)
        make_post(status=PostStatus.PENDING)
        page = DjangoPostRepository().list(
            PostFilter(statuses=(PostStatus.APPROVED,)), PageRequest(limit=10)
        )
        assert len(page.items) == 1
        assert page.items[0].status is PostStatus.APPROVED

    def test_map_markers_are_approved_only(self):
        make_post(status=PostStatus.APPROVED)
        make_post(status=PostStatus.PENDING)
        markers = DjangoPostRepository().list_map_markers()
        assert len(markers) == 1

    def test_cursor_pagination_walks_all(self):
        for _ in range(5):
            make_post(status=PostStatus.APPROVED)
        repo = DjangoPostRepository()
        seen, cursor = [], None
        for _ in range(10):  # guard against infinite loop
            page = repo.list(PostFilter(statuses=(PostStatus.APPROVED,)),
                             PageRequest(limit=2, cursor=cursor))
            seen.extend(p.id for p in page.items)
            cursor = page.next_cursor
            if cursor is None:
                break
        assert len(seen) == 5
        assert len(set(seen)) == 5  # no duplicates, no gaps


class TestEngagementRepository:
    def test_partial_unique_index_blocks_duplicate_like(self):
        """The DB constraint, not a pre-check, is the guard (LLD §7.2, §9.3)."""
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)
        repo = DjangoEngagementRepository()

        repo.add(Engagement(None, post.id, EngagementType.LIKE, bob.id, created=NOW))
        with pytest.raises(AlreadyLiked):
            repo.add(Engagement(None, post.id, EngagementType.LIKE, bob.id, created=NOW))

        assert repo.count(post.id, EngagementType.LIKE) == 1

    def test_anonymous_likes_are_not_deduplicated(self):
        """actor_user IS NULL is outside the partial index, so anonymous likes stack — which
        is exactly why DEC-1 makes them worth zero points."""
        alice = make_user("alice")
        post = make_post(reporter_id=alice.id)
        repo = DjangoEngagementRepository()

        repo.add(Engagement(None, post.id, EngagementType.LIKE, None, created=NOW))
        repo.add(Engagement(None, post.id, EngagementType.LIKE, None, created=NOW))

        assert repo.count(post.id, EngagementType.LIKE) == 2

    def test_relike_after_unlike(self):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)
        repo = DjangoEngagementRepository()

        repo.add(Engagement(None, post.id, EngagementType.LIKE, bob.id, created=NOW))
        assert repo.remove_like(post.id, bob.id) is True
        repo.add(Engagement(None, post.id, EngagementType.LIKE, bob.id, created=NOW))
        assert repo.count(post.id, EngagementType.LIKE) == 1

    def test_denormalised_owner_is_captured(self):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)
        DjangoEngagementRepository().add(
            Engagement(None, post.id, EngagementType.LIKE, bob.id, created=NOW)
        )
        from adapters.persistence.django_orm import models as orm

        row = orm.Engagement.objects.get(post_id=post.id, actor_user_id=bob.id)
        assert row.post_owner_user_id == alice.id
