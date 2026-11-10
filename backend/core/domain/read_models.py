"""Read models and query filters.

Read models are shapes the domain hands out for display; they are not entities and have no
behaviour. Filters are what use cases pass to repositories.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from core.domain.ids import ModerationLogId, PostId, UserId
from core.domain.value_objects import ImageRef, ModerationAction, PostStatus, Severity


@dataclass(frozen=True, slots=True)
class PostFilter:
    """Orthogonal filters (LLD §8.4).

    Replaces the legacy overloaded ``filter=today|severity_3|accepted`` parameter, which
    could not express "accepted AND severity 3".

    ``statuses`` is NOT a public query parameter: public use cases pin it to APPROVED and
    only admin use cases pass anything else.
    """

    statuses: tuple[PostStatus, ...] = (PostStatus.APPROVED,)
    severity: Severity | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    reporter_id: UserId | None = None
    include_deleted: bool = False


@dataclass(frozen=True, slots=True)
class MapMarker:
    """Thin marker for the map endpoint.

    Deliberately not a Post: the map wants thousands of these, the feed wants twenty full
    records. Same query for both was the legacy mistake (LLD §8.4).
    """

    id: PostId
    lat: float
    lon: float
    severity: Severity
    image: ImageRef | None = None


@dataclass(frozen=True, slots=True)
class AdminMapMarker:
    """Like MapMarker but with status - the admin density map shows all non-deleted reports,
    not just approved ones, so pending hot-spots are visible for triage (LLD §8.4)."""

    id: PostId
    lat: float
    lon: float
    severity: Severity
    status: PostStatus
    image: ImageRef | None = None


@dataclass(frozen=True, slots=True)
class LeaderboardRow:
    user_id: UserId
    username: str
    full_name: str
    points: int
    rank: int
    avatar: ImageRef | None = None


@dataclass(frozen=True, slots=True)
class AuditLogEntry:
    """A moderation action for the admin audit screen, with the admin's name resolved."""

    id: ModerationLogId
    post_id: PostId
    admin_name: str
    action: ModerationAction
    reason: str
    at: datetime


@dataclass(frozen=True, slots=True)
class Contribution:
    """Replaces the legacy contribution view, which hardcoded levels and zeroed reviews."""

    user_id: UserId
    total_points: int
    posts_approved: int
    likes_received: int
    likes_given: int
    level: int
    level_title: str
    points_to_next_level: int | None  # None => max level reached
    progress_percentage: float
    referrals: int = 0  # no referral system yet


@dataclass(frozen=True, slots=True)
class EarnedBadge:
    code: str
    name: str
    description: str
    icon: str
    earned_at: datetime


@dataclass(frozen=True, slots=True)
class WeeklyPoint:
    week: date  # the Monday the week starts on
    submitted: int
    approved: int


@dataclass(frozen=True, slots=True)
class PostAnalytics:
    """Dashboard time-series: submissions vs approvals per week, plus active contributors."""

    over_time: list[WeeklyPoint]
    active_users: int


@dataclass(frozen=True, slots=True)
class StatusCounts:
    counts: dict[PostStatus, int] = field(default_factory=dict)

    def get(self, status: PostStatus) -> int:
        return self.counts.get(status, 0)

    @property
    def total(self) -> int:
        return sum(self.counts.values())
