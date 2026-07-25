"""Repository ports.

Every method accepts and returns DOMAIN types. Never an ORM model, never a QuerySet: a lazy
queryset crossing this boundary would leak persistence semantics into the domain and make
the port fiction.

These ABCs are the strategy interfaces. Implementations (Django ORM, in-memory fakes, a
future ORM-based or NoSQL leaderboard) are selected in the composition root.
"""

from __future__ import annotations  # `def list(...)` shadows the builtin in class bodies

from abc import ABC, abstractmethod
from datetime import datetime

from core.domain.entities import (
    OTP,
    BadgeRule,
    ContactMessage,
    ContactPage,
    Engagement,
    Feedback,
    LevelRule,
    Post,
    PostModerationLog,
    SiteConfig,
    User,
    UserBadge,
)
from core.domain.ids import ContactMessageId, PostId, UserId
from core.domain.pagination import Page, PageRequest
from core.domain.points import Rules
from core.domain.read_models import (
    AdminMapMarker,
    Contribution,
    LeaderboardRow,
    MapMarker,
    PostAnalytics,
    PostFilter,
    StatusCounts,
)
from core.domain.value_objects import EngagementType, OTPPurpose, Role


class UserRepository(ABC):
    @abstractmethod
    def get(self, id: UserId) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def add(self, user: User, password: str) -> User:
        """Raises UsernameTaken / EmailTaken."""

    @abstractmethod
    def update(self, user: User) -> User: ...

    @abstractmethod
    def set_password(self, id: UserId, password: str) -> None: ...

    @abstractmethod
    def verify_password(self, id: UserId, password: str) -> bool: ...

    @abstractmethod
    def set_role(self, id: UserId, role: Role) -> User: ...

    @abstractmethod
    def set_active(self, id: UserId, is_active: bool) -> User: ...

    @abstractmethod
    def delete(self, id: UserId) -> None:
        """Hard delete. Their posts' reporter FK is SET_NULL (kept, anonymised)."""

    @abstractmethod
    def touch_last_login(self, id: UserId, at: datetime) -> None: ...

    @abstractmethod
    def list(self, page: PageRequest) -> Page[User]: ...


class OTPRepository(ABC):
    @abstractmethod
    def add(self, otp: OTP) -> OTP: ...

    @abstractmethod
    def latest_valid_for(self, username: str, purpose: OTPPurpose, now: datetime) -> OTP | None:
        """Correctness must not depend on cleanup running: filters on expiry (LLD §9.4)."""

    @abstractmethod
    def invalidate_for(self, username: str, purpose: OTPPurpose) -> None: ...

    @abstractmethod
    def purge_expired(self, now: datetime) -> int:
        """Postgres has no TTL index; this replaces the legacy Mongo behaviour."""


class PostRepository(ABC):
    @abstractmethod
    def get(self, id: PostId) -> Post | None: ...

    @abstractmethod
    def add(self, post: Post) -> Post: ...

    @abstractmethod
    def update(self, post: Post) -> Post: ...

    @abstractmethod
    def list(self, filter: PostFilter, page: PageRequest) -> Page[Post]: ...

    @abstractmethod
    def list_map_markers(self) -> list[MapMarker]:
        """Approved posts only, thin projection — never the full record (LLD §8.4)."""

    @abstractmethod
    def list_admin_map_markers(self) -> list[AdminMapMarker]:
        """All non-deleted posts (any status), thin projection — for the admin density map."""

    @abstractmethod
    def counts_by_status(self) -> StatusCounts: ...

    @abstractmethod
    def analytics(self, since: datetime) -> PostAnalytics:
        """Weekly submitted/approved series since `since`, plus the count of distinct
        authenticated contributors in that window — for the admin dashboard."""


class EngagementRepository(ABC):
    @abstractmethod
    def add(self, engagement: Engagement) -> Engagement:
        """Raises AlreadyLiked.

        The adapter MUST translate the database's unique-constraint violation into
        AlreadyLiked rather than checking first: a check-then-act read would let a
        concurrent double-like through (LLD §7.2).
        """

    @abstractmethod
    def get_like(self, post_id: PostId, actor_id: UserId) -> Engagement | None: ...

    @abstractmethod
    def remove_like(self, post_id: PostId, actor_id: UserId) -> bool:
        """Returns False when there was nothing to remove."""

    @abstractmethod
    def count(self, post_id: PostId, type: EngagementType) -> int: ...

    @abstractmethod
    def counts_for(self, post_ids: list[PostId], type: EngagementType) -> dict[PostId, int]:
        """Batch lookup — avoids N+1 when serializing a page of posts."""

    @abstractmethod
    def liked_post_ids(self, post_ids: list[PostId], actor_id: UserId) -> set[PostId]:
        """Which of these posts the actor has already liked (for `liked_by_me`)."""


class PointRuleRepository(ABC):
    @abstractmethod
    def active_rules(self) -> Rules:
        """Rule code -> effective points. Inactive rules resolve to 0, not absent."""


class LevelRuleRepository(ABC):
    @abstractmethod
    def all(self) -> list[LevelRule]: ...


class LeaderboardRepository(ABC):
    """The leaderboard calculation strategy.

    The default implementation is raw Postgres SQL (LLD §5.4). Swapping in an ORM or NoSQL
    implementation means implementing this port and passing the shared contract suite in
    tests/contract/ — the rules live in core.domain.points AND in SQL, so that suite is
    what stops them drifting.
    """

    @abstractmethod
    def top(self, since: datetime | None, rules: Rules, page: PageRequest) -> Page[LeaderboardRow]:
        """`since` is the inclusive period lower bound (None = all-time), already computed by
        the use case from the period, the clock, and the configured week-start. The adapter
        only filters by it — no time/timezone/period logic lives in the adapter."""

    @abstractmethod
    def contribution_for(
        self,
        user_id: UserId,
        rules: Rules,
        levels: list[LevelRule],
    ) -> Contribution: ...


class FeedbackRepository(ABC):
    @abstractmethod
    def add(self, feedback: Feedback) -> Feedback: ...

    @abstractmethod
    def list(self, page: PageRequest) -> Page[Feedback]: ...


class ContactRepository(ABC):
    @abstractmethod
    def get_page(self) -> ContactPage: ...

    @abstractmethod
    def save_page(self, page: ContactPage) -> ContactPage: ...

    @abstractmethod
    def add_message(self, message: ContactMessage) -> ContactMessage: ...

    @abstractmethod
    def get_message(self, id: ContactMessageId) -> ContactMessage | None: ...

    @abstractmethod
    def update_message(self, message: ContactMessage) -> ContactMessage: ...

    @abstractmethod
    def list_messages(self, page: PageRequest) -> Page[ContactMessage]: ...


class ModerationLogRepository(ABC):
    @abstractmethod
    def add(self, entry: PostModerationLog) -> PostModerationLog: ...

    @abstractmethod
    def list_for_post(self, post_id: PostId) -> list[PostModerationLog]: ...

    @abstractmethod
    def list(self, page: PageRequest) -> Page[PostModerationLog]:
        """All actions, newest first — for the admin audit screen."""


class SiteConfigRepository(ABC):
    @abstractmethod
    def get(self) -> SiteConfig:
        """Always returns a config — defaults if none has been saved yet."""

    @abstractmethod
    def save(self, config: SiteConfig) -> SiteConfig: ...


class BadgeRepository(ABC):
    @abstractmethod
    def active_rules(self) -> list[BadgeRule]: ...

    @abstractmethod
    def earned_codes(self, user_id: UserId) -> set[str]: ...

    @abstractmethod
    def award(self, user_id: UserId, code: str, at) -> None:
        """Idempotent — awarding an already-held badge is a no-op."""

    @abstractmethod
    def list_earned(self, user_id: UserId) -> list[UserBadge]: ...

    @abstractmethod
    def rules_by_code(self) -> dict[str, BadgeRule]: ...
