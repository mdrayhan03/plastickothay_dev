"""Leaderboard contract suite — the guard against SQL/Python rule drift (LLD §5.4, B5).

The point rules live in two places: core.domain.points (the reference, used by the fake) and
the Django ORM aggregation in adapters. This suite runs identical scenarios against BOTH and
asserts identical numbers. Any future implementation (raw SQL, materialized view, NoSQL) must
pass this same suite to be considered done.

Each scenario builds the same world through a builder, then asserts the contribution/leaderboard
match across implementations.
"""

from datetime import UTC, datetime

import pytest

from core.domain.pagination import PageRequest
from core.domain.value_objects import Role
from tests.fakes.seed import DEFAULT_LEVEL_RULES, DEFAULT_POINT_RULES

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


# --- the two implementations under test ------------------------------------


class FakeBackend:
    """Reference: in-memory repos delegating to core.domain.points."""

    name = "fake"

    def __init__(self):
        from tests.fakes.repositories import (
            InMemoryEngagementRepository,
            InMemoryLeaderboardRepository,
            InMemoryPostRepository,
            InMemoryUserRepository,
        )
        from tests.fakes.system import FakeClock

        self.clock = FakeClock(NOW)
        self.users = InMemoryUserRepository()
        self.posts = InMemoryPostRepository()
        self.engagements = InMemoryEngagementRepository()
        self.leaderboard = InMemoryLeaderboardRepository(
            self.posts, self.engagements, self.users, self.clock
        )

    def add_user(self, username, role=Role.USER):
        from core.domain.entities import User

        return self.users.add(
            User(id=None, username=username, email=f"{username}@e.com", first_name=username,
                 last_name="T", phone="x", role=role, is_verified=True, is_active=True,
                 date_joined=NOW),
            password="x",
        )

    def add_post(self, reporter_id, status, approved_at=None):
        from core.domain.entities import Post
        from core.domain.value_objects import GeoPoint, ImageRef, PostStatus, Reporter, Severity

        return self.posts.add(
            Post(id=None, reporter=Reporter("R", "r@e.com", "x"), reporter_id=reporter_id,
                 severity=Severity.MODERATE, image=ImageRef("fake", "i"),
                 location=GeoPoint(23.8, 90.4), description="d", status=status, created=NOW,
                 approved_at=approved_at if status is PostStatus.APPROVED else None)
        )

    def add_like(self, post_id, actor_id, created=NOW):
        from core.domain.entities import Engagement
        from core.domain.value_objects import EngagementType

        return self.engagements.add(
            Engagement(id=None, post_id=post_id, type=EngagementType.LIKE,
                       actor_id=actor_id, created=created)
        )


class DjangoBackend:
    """The ORM implementation."""

    name = "django"

    def __init__(self):
        from adapters.persistence.django_orm.leaderboard import DjangoLeaderboardRepository
        from adapters.persistence.django_orm.repositories import (
            DjangoEngagementRepository,
            DjangoPostRepository,
            DjangoUserRepository,
        )

        self.users = DjangoUserRepository()
        self.posts = DjangoPostRepository()
        self.engagements = DjangoEngagementRepository()
        self.leaderboard = DjangoLeaderboardRepository()

    def add_user(self, username, role=Role.USER):
        from core.domain.entities import User

        return self.users.add(
            User(id=None, username=username, email=f"{username}@e.com", first_name=username,
                 last_name="T", phone="x", role=role, is_verified=True, is_active=True,
                 date_joined=NOW),
            password="x",
        )

    def add_post(self, reporter_id, status, approved_at=None):
        from core.domain.entities import Post
        from core.domain.value_objects import GeoPoint, ImageRef, PostStatus, Reporter, Severity

        return self.posts.add(
            Post(id=None, reporter=Reporter("R", "r@e.com", "x"), reporter_id=reporter_id,
                 severity=Severity.MODERATE, image=ImageRef("fake", "i"),
                 location=GeoPoint(23.8, 90.4), description="d", status=status, created=NOW,
                 approved_at=approved_at if status is PostStatus.APPROVED else None)
        )

    def add_like(self, post_id, actor_id, created=NOW):
        from core.domain.entities import Engagement
        from core.domain.value_objects import EngagementType

        return self.engagements.add(
            Engagement(id=None, post_id=post_id, type=EngagementType.LIKE,
                       actor_id=actor_id, created=created)
        )


BACKENDS = [FakeBackend, DjangoBackend]


@pytest.fixture(params=BACKENDS, ids=[b.name for b in BACKENDS])
def backend(request, db):
    """Parametrized over both implementations. `db` gives the Django one a database."""
    return request.param()


def points_of(backend, user_id) -> int:
    return backend.leaderboard.contribution_for(
        user_id, DEFAULT_POINT_RULES, DEFAULT_LEVEL_RULES
    ).total_points


# --- the shared scenarios --------------------------------------------------


class TestLeaderboardContract:
    def test_approved_post_awards_owner(self, backend):
        from core.domain.value_objects import PostStatus

        alice = backend.add_user("alice")
        backend.add_post(alice.id, PostStatus.APPROVED, approved_at=NOW)
        assert points_of(backend, alice.id) == 100

    def test_authenticated_like_pays_both_sides(self, backend):
        from core.domain.value_objects import PostStatus

        alice, bob = backend.add_user("alice"), backend.add_user("bob")
        post = backend.add_post(alice.id, PostStatus.APPROVED, approved_at=NOW)
        backend.add_like(post.id, bob.id)
        assert points_of(backend, alice.id) == 103  # post + like received
        assert points_of(backend, bob.id) == 1  # like given

    def test_anonymous_like_awards_nobody(self, backend):
        from core.domain.value_objects import PostStatus

        alice = backend.add_user("alice")
        post = backend.add_post(alice.id, PostStatus.APPROVED, approved_at=NOW)
        backend.add_like(post.id, None)
        assert points_of(backend, alice.id) == 100  # post only

    def test_self_like_awards_zero(self, backend):
        from core.domain.value_objects import PostStatus

        alice = backend.add_user("alice")
        post = backend.add_post(alice.id, PostStatus.APPROVED, approved_at=NOW)
        backend.add_like(post.id, alice.id)
        assert points_of(backend, alice.id) == 100

    @pytest.mark.parametrize("status_name", ["PENDING", "HIDDEN"])
    def test_like_on_non_public_post_awards_nothing(self, backend, status_name):
        from core.domain.value_objects import PostStatus

        alice, bob = backend.add_user("alice"), backend.add_user("bob")
        post = backend.add_post(alice.id, getattr(PostStatus, status_name))
        backend.add_like(post.id, bob.id)
        assert points_of(backend, alice.id) == 0
        assert points_of(backend, bob.id) == 0

    def test_anonymous_post_awards_nobody(self, backend):
        from core.domain.value_objects import PostStatus

        bob = backend.add_user("bob")
        post = backend.add_post(None, PostStatus.APPROVED, approved_at=NOW)
        backend.add_like(post.id, bob.id)  # like on anon post — no receiver, no giver credit
        assert points_of(backend, bob.id) == 0

    def test_leaderboard_ranks_by_points(self, backend):
        from core.domain.value_objects import PostStatus

        alice, bob = backend.add_user("alice"), backend.add_user("bob")
        backend.add_post(alice.id, PostStatus.APPROVED, approved_at=NOW)
        p = backend.add_post(bob.id, PostStatus.APPROVED, approved_at=NOW)
        backend.add_post(bob.id, PostStatus.APPROVED, approved_at=NOW)
        backend.add_like(p.id, alice.id)  # bob gets +3, alice +1

        rows = backend.leaderboard.top(None, DEFAULT_POINT_RULES, PageRequest(limit=10))
        assert [(r.username, r.points) for r in rows.items] == [("bob", 203), ("alice", 101)]
        assert rows.items[0].rank == 1

    def test_weekly_period_excludes_old_approvals(self, backend):
        from core.domain.periods import period_start
        from core.domain.value_objects import Period, PostStatus

        alice = backend.add_user("alice")
        backend.add_post(alice.id, PostStatus.APPROVED,
                         approved_at=datetime(2026, 1, 1, tzinfo=UTC))  # old

        # The use case computes `since`; here we compute it the same way and pass it in.
        since = period_start(Period.WEEK, NOW)
        rows = backend.leaderboard.top(since, DEFAULT_POINT_RULES, PageRequest(limit=10))
        # Old approval falls outside this week → alice not on the weekly board.
        assert all(r.username != "alice" for r in rows.items)

    def test_inactive_rule_contributes_zero(self, backend):
        from core.domain.value_objects import PostStatus

        rules = {**DEFAULT_POINT_RULES, "like_received": 0, "like_given": 0}
        alice, bob = backend.add_user("alice"), backend.add_user("bob")
        post = backend.add_post(alice.id, PostStatus.APPROVED, approved_at=NOW)
        backend.add_like(post.id, bob.id)

        a = backend.leaderboard.contribution_for(alice.id, rules, DEFAULT_LEVEL_RULES)
        assert a.total_points == 100  # like no longer pays
        assert a.likes_received == 1  # but still counted
