"""Point rules - the specification, in pure Python.

Points are DERIVED from current state (LLD DEC-2): there is no ledger and no score table.
A user's score is a function of current post statuses x current engagements x active rules.
Hiding a post therefore strips its points and its likes' points automatically, and
un-hiding restores them, with no reversal code anywhere.

  THIS MODULE IS THE SPECIFICATION. The production leaderboard is raw SQL living in a
  repository adapter, so these rules exist in two places and CAN DRIFT. The shared
  contract test suite (tests/contract/) runs identical scenarios against this
  implementation and every repository implementation. Any new calculation strategy is
  only done when it passes that suite.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime

from core.domain.entities import Engagement, LevelRule, Post
from core.domain.ids import UserId
from core.domain.value_objects import EngagementType

RULE_POST_APPROVED = "post_approved"
RULE_LIKE_RECEIVED = "like_received"
RULE_LIKE_GIVEN = "like_given"
RULE_COMMENT_RECEIVED = "comment_received"
RULE_COMMENT_GIVEN = "comment_given"

ALL_RULE_CODES = (
    RULE_POST_APPROVED,
    RULE_LIKE_RECEIVED,
    RULE_LIKE_GIVEN,
    RULE_COMMENT_RECEIVED,
    RULE_COMMENT_GIVEN,
)

Rules = Mapping[str, int]  # rule code -> effective points (0 when inactive)


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    posts_approved: int = 0
    likes_received: int = 0
    likes_given: int = 0
    points: int = 0


def post_earns_points(post: Post, since: datetime | None = None) -> bool:
    """A post scores for its owner only if it is publicly approved and attributable."""
    if post.reporter_id is None:  # anonymous reports earn nobody points
        return False
    if not post.is_public:
        return False
    # Bucketed by approval date, not creation date (LLD DEC-3).
    if since is not None and (post.approved_at is None or post.approved_at < since):
        return False
    return True


def engagement_earns_points(
    engagement: Engagement,
    post: Post,
    since: datetime | None = None,
) -> bool:
    """Whether an engagement moves anyone's score.

    All four conditions must hold (LLD §5.3):
      1. the actor is authenticated - anonymous engagement awards nothing to ANYONE,
         including the post owner. This is a security control, not a product choice
         (DEC-1): an anonymous liker has no stable identity, so no unique constraint can
         bind them, and awarding the owner would let a shell loop print points forever.
      2. the post is publicly approved.
      3. the post is attributable to a user.
      4. the actor is not the post owner - self-engagement awards zero to both sides.
    """
    if engagement.actor_id is None:
        return False
    if not post.is_public:
        return False
    if post.reporter_id is None:
        return False
    if engagement.actor_id == post.reporter_id:
        return False
    if since is not None and (engagement.created is None or engagement.created < since):
        return False
    return True


def _received_rule(engagement_type: EngagementType) -> str:
    return {
        EngagementType.LIKE: RULE_LIKE_RECEIVED,
        EngagementType.COMMENT: RULE_COMMENT_RECEIVED,
    }[engagement_type]


def _given_rule(engagement_type: EngagementType) -> str:
    return {
        EngagementType.LIKE: RULE_LIKE_GIVEN,
        EngagementType.COMMENT: RULE_COMMENT_GIVEN,
    }[engagement_type]


def compute_scores(
    posts: Iterable[Post],
    engagements: Iterable[Engagement],
    rules: Rules,
    since: datetime | None = None,
) -> dict[UserId, ScoreBreakdown]:
    """Reference implementation of every user's score."""
    by_id = {p.id: p for p in posts if p.id is not None}
    acc: dict[UserId, dict[str, int]] = {}

    def bump(user_id: UserId, field: str, points: int) -> None:
        row = acc.setdefault(
            user_id, {"posts_approved": 0, "likes_received": 0, "likes_given": 0, "points": 0}
        )
        row[field] += 1
        row["points"] += points

    for post in by_id.values():
        if post_earns_points(post, since):
            assert post.reporter_id is not None  # guaranteed by post_earns_points
            bump(post.reporter_id, "posts_approved", rules.get(RULE_POST_APPROVED, 0))

    for e in engagements:
        post = by_id.get(e.post_id)
        if post is None or not engagement_earns_points(e, post, since):
            continue
        assert e.actor_id is not None and post.reporter_id is not None

        if e.type is EngagementType.LIKE:
            bump(post.reporter_id, "likes_received", rules.get(_received_rule(e.type), 0))
            bump(e.actor_id, "likes_given", rules.get(_given_rule(e.type), 0))
        else:
            # Comments are modelled but their rules ship inactive, so points resolve to 0.
            bump(post.reporter_id, "likes_received", 0)
            bump(e.actor_id, "likes_given", 0)

    return {uid: ScoreBreakdown(**row) for uid, row in acc.items()}


def compute_breakdown(
    user_id: UserId,
    posts: Iterable[Post],
    engagements: Iterable[Engagement],
    rules: Rules,
    since: datetime | None = None,
) -> ScoreBreakdown:
    return compute_scores(posts, engagements, rules, since).get(user_id, ScoreBreakdown())


# --- levels ----------------------------------------------------------------
# The legacy code hardcoded "every 5 points = 1 level"; levels are now table-driven.


def level_for(points: int, levels: Iterable[LevelRule]) -> LevelRule:
    ordered = sorted(levels, key=lambda level: level.min_points)
    if not ordered:
        raise ValueError("At least one LevelRule must be configured")
    current = ordered[0]
    for level in ordered:
        if points >= level.min_points:
            current = level
        else:
            break
    return current


def next_level(points: int, levels: Iterable[LevelRule]) -> LevelRule | None:
    ordered = sorted(levels, key=lambda level: level.min_points)
    for level in ordered:
        if level.min_points > points:
            return level
    return None  # max level reached


def level_progress(points: int, levels: Iterable[LevelRule]) -> tuple[int | None, float]:
    """Returns ``(points_to_next_level, progress_percentage)``.

    ``(None, 100.0)`` at max level.
    """
    ordered = sorted(levels, key=lambda level: level.min_points)
    current = level_for(points, ordered)
    upcoming = next_level(points, ordered)
    if upcoming is None:
        return None, 100.0

    span = upcoming.min_points - current.min_points
    if span <= 0:
        return 0, 100.0
    earned = points - current.min_points
    return upcoming.min_points - points, round(earned / span * 100, 2)
