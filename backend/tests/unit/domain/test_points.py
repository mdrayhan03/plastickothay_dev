"""The rules the whole product rests on.

Every one of these runs with no database, no Django, and no network. This file is the
executable form of LLD §5.3 and the B0 exit criteria.
"""

from datetime import UTC, datetime

import pytest

from core.domain.entities import Engagement, Post
from core.domain.ids import PostId, UserId
from core.domain.points import (
    RULE_LIKE_GIVEN,
    RULE_LIKE_RECEIVED,
    RULE_POST_APPROVED,
    ScoreBreakdown,
    compute_scores,
    level_for,
    level_progress,
    next_level,
)
from core.domain.value_objects import (
    EngagementType,
    GeoPoint,
    ImageRef,
    PostStatus,
    Reporter,
    Severity,
)
from tests.fakes.seed import DEFAULT_LEVEL_RULES, DEFAULT_POINT_RULES

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)

ALICE = UserId(1)
BOB = UserId(2)


def make_post(
    post_id: int,
    reporter_id: UserId | None,
    status: PostStatus = PostStatus.APPROVED,
    approved_at: datetime | None = NOW,
    deleted_at: datetime | None = None,
) -> Post:
    return Post(
        id=PostId(post_id),
        reporter=Reporter("R", "r@example.com", "+880"),
        reporter_id=reporter_id,
        severity=Severity.MODERATE,
        image=ImageRef("fake", f"img-{post_id}"),
        location=GeoPoint(23.8103, 90.4125),
        description="d",
        status=status,
        created=NOW,
        approved_at=approved_at if status is PostStatus.APPROVED else None,
        deleted_at=deleted_at,
    )


def like(post_id: int, actor_id: UserId | None, at: datetime = NOW) -> Engagement:
    return Engagement(
        id=None,
        post_id=PostId(post_id),
        type=EngagementType.LIKE,
        actor_id=actor_id,
        created=at,
    )


def score(posts, engagements, rules=None, since=None) -> dict[UserId, ScoreBreakdown]:
    return compute_scores(posts, engagements, rules or DEFAULT_POINT_RULES, since)


class TestPostPoints:
    def test_approved_post_earns_its_owner(self):
        result = score([make_post(1, ALICE)], [])
        assert result[ALICE].points == 100
        assert result[ALICE].posts_approved == 1

    @pytest.mark.parametrize("status", [PostStatus.PENDING, PostStatus.HIDDEN, PostStatus.REJECTED])
    def test_non_approved_post_earns_nothing(self, status):
        assert score([make_post(1, ALICE, status=status)], []) == {}

    def test_anonymous_post_earns_nobody(self):
        assert score([make_post(1, None)], []) == {}

    def test_soft_deleted_post_earns_nothing(self):
        post = make_post(1, ALICE, deleted_at=NOW)
        assert score([post], []) == {}


class TestLikePoints:
    def test_authenticated_like_pays_both_sides(self):
        result = score([make_post(1, ALICE)], [like(1, BOB)])
        assert result[ALICE].points == 100 + 3  # post + like received
        assert result[ALICE].likes_received == 1
        assert result[BOB].points == 1  # like given
        assert result[BOB].likes_given == 1

    def test_anonymous_like_awards_nobody(self):
        """DEC-1. The owner must NOT be paid for an anonymous like.

        Otherwise a five-line script with no account prints unlimited points.
        """
        result = score([make_post(1, ALICE)], [like(1, None)])
        assert result[ALICE].points == 100  # post only — no like points
        assert result[ALICE].likes_received == 0

    def test_self_like_awards_zero_to_both_sides(self):
        result = score([make_post(1, ALICE)], [like(1, ALICE)])
        assert result[ALICE].points == 100
        assert result[ALICE].likes_received == 0
        assert result[ALICE].likes_given == 0

    @pytest.mark.parametrize("status", [PostStatus.PENDING, PostStatus.HIDDEN])
    def test_like_on_non_public_post_awards_nothing(self, status):
        assert score([make_post(1, ALICE, status=status)], [like(1, BOB)]) == {}

    def test_like_on_anonymous_post_awards_the_liker_nothing(self):
        # Nobody owns the post, so there is no receiver and no giver credit.
        assert score([make_post(1, None)], [like(1, BOB)]) == {}

    def test_like_for_missing_post_is_ignored(self):
        assert score([], [like(999, BOB)]) == {}


class TestStatusTransitionsMovePointsAutomatically:
    """The payoff of the derived model (DEC-2): no reversal code exists, yet hiding a post
    strips its points AND its likes' points, and un-hiding restores them."""

    def test_hiding_strips_post_and_engagement_points(self):
        post = make_post(1, ALICE)
        likes = [like(1, BOB)]
        assert score([post], likes)[ALICE].points == 103

        post.hide()

        assert score([post], likes) == {}  # Alice's 103 and Bob's 1 both gone

    def test_unhiding_restores_everything(self):
        post = make_post(1, ALICE)
        likes = [like(1, BOB)]
        post.hide()
        assert score([post], likes) == {}

        post.unhide(NOW)

        restored = score([post], likes)
        assert restored[ALICE].points == 103
        assert restored[BOB].points == 1

    def test_rejecting_strips_points(self):
        post = make_post(1, ALICE)
        likes = [like(1, BOB)]
        post.reject(NOW)
        assert score([post], likes) == {}


class TestRuleChanges:
    def test_inactive_rule_contributes_zero(self):
        """Deactivating a rule stops it PAYING, but the engagement is still counted.

        The distinction matters for the contribution page: Bob really did give a like, so
        it stays visible at zero points. Contrast with an anonymous like, which is never
        counted for either side because it can never earn (DEC-1).
        """
        rules = {**DEFAULT_POINT_RULES, RULE_LIKE_RECEIVED: 0, RULE_LIKE_GIVEN: 0}
        result = score([make_post(1, ALICE)], [like(1, BOB)], rules)

        assert result[ALICE].points == 100  # post only — the like no longer pays
        assert result[ALICE].likes_received == 1  # but is still counted
        assert result[BOB].points == 0
        assert result[BOB].likes_given == 1

    def test_inactive_rule_keeps_the_liker_off_the_leaderboard(
        self,
    ):
        """Zero-point users must not appear: `top()` filters on points > 0."""
        rules = {**DEFAULT_POINT_RULES, RULE_LIKE_RECEIVED: 0, RULE_LIKE_GIVEN: 0}
        result = score([make_post(1, ALICE)], [like(1, BOB)], rules)
        assert [uid for uid, b in result.items() if b.points > 0] == [ALICE]

    def test_rule_change_is_retroactive(self):
        """DEC-2: this is the accepted cost, mitigated by POL-1 (announce first)."""
        posts = [make_post(1, ALICE)]
        assert score(posts, [])[ALICE].points == 100
        assert (
            score(posts, [], {**DEFAULT_POINT_RULES, RULE_POST_APPROVED: 150})[ALICE].points == 150
        )


class TestPeriodWindow:
    def test_since_excludes_older_approvals(self):
        old = make_post(1, ALICE, approved_at=datetime(2026, 1, 1, tzinfo=UTC))
        recent = make_post(2, ALICE, approved_at=datetime(2026, 7, 17, tzinfo=UTC))
        window = datetime(2026, 7, 1, tzinfo=UTC)

        result = score([old, recent], [], since=window)

        assert result[ALICE].posts_approved == 1  # only the recent one
        assert result[ALICE].points == 100

    def test_posts_bucket_by_approval_not_creation(self):
        """DEC-3: filed in June, approved in July => counts in July."""
        post = make_post(1, ALICE, approved_at=datetime(2026, 7, 17, tzinfo=UTC))
        post.created = datetime(2026, 6, 1, tzinfo=UTC)

        assert score([post], [], since=datetime(2026, 7, 1, tzinfo=UTC))[ALICE].points == 100

    def test_since_excludes_older_likes(self):
        post = make_post(1, ALICE)
        old_like = like(1, BOB, at=datetime(2026, 1, 1, tzinfo=UTC))

        result = score([post], [old_like], since=datetime(2026, 7, 1, tzinfo=UTC))

        assert result[ALICE].likes_received == 0
        assert BOB not in result


class TestLevels:
    @pytest.mark.parametrize(
        "points,expected_level",
        [(0, 1), (99, 1), (100, 2), (299, 2), (300, 3), (700, 4), (1500, 5), (99_999, 5)],
    )
    def test_level_for(self, points, expected_level):
        assert level_for(points, DEFAULT_LEVEL_RULES).level == expected_level

    def test_next_level(self):
        assert next_level(0, DEFAULT_LEVEL_RULES).level == 2
        assert next_level(1500, DEFAULT_LEVEL_RULES) is None

    def test_progress_halfway(self):
        to_next, pct = level_progress(200, DEFAULT_LEVEL_RULES)  # level 2: 100..300
        assert to_next == 100
        assert pct == 50.0

    def test_progress_at_max_level(self):
        assert level_progress(2000, DEFAULT_LEVEL_RULES) == (None, 100.0)

    def test_level_for_requires_configuration(self):
        with pytest.raises(ValueError):
            level_for(0, [])
