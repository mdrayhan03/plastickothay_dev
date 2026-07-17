"""Domain entities — plain dataclasses with identity.

These are NOT ORM models and must never gain a ``.save()``. The persistence adapter maps
between these and Django models (LLD §2.2). If this module ever imports Django, the DB port
is fiction and the architecture is decorative.
"""

from dataclasses import dataclass, field
from datetime import datetime

from core.domain.ids import (
    ContactMessageId,
    EngagementId,
    FeedbackId,
    ModerationLogId,
    OTPId,
    PostId,
    UserId,
)
from core.domain.value_objects import (
    EngagementType,
    GeoPoint,
    ImageRef,
    ModerationAction,
    OTPPurpose,
    PostStatus,
    Reporter,
    Role,
    Severity,
    SocialLink,
)


@dataclass
class User:
    id: UserId | None
    username: str
    email: str
    first_name: str
    last_name: str
    phone: str
    role: Role = Role.USER
    is_verified: bool = False  # completed OTP
    is_active: bool = True  # not banned — Django's meaning
    date_joined: datetime | None = None
    last_login: datetime | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def can_sign_in(self) -> bool:
        return self.is_verified and self.is_active

    def as_reporter(self) -> Reporter:
        """Reporter block for an authenticated submission.

        Client-supplied contact details are ignored for logged-in users, otherwise a user
        could attach a stranger's email and phone to a report (LLD §7.1).
        """
        return Reporter(name=self.full_name, email=self.email, phone=self.phone)


@dataclass
class OTP:
    id: OTPId | None
    username: str
    code: int
    purpose: OTPPurpose
    created_at: datetime
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def matches(self, code: int) -> bool:
        return self.code == code


@dataclass
class Post:
    id: PostId | None
    reporter: Reporter  # ALWAYS present
    reporter_id: UserId | None  # None => anonymous submission
    severity: Severity
    image: ImageRef
    location: GeoPoint
    description: str
    status: PostStatus = PostStatus.PENDING
    created: datetime | None = None
    approved_at: datetime | None = None  # first approval only — stable leaderboard bucket
    deleted_at: datetime | None = None

    @property
    def is_public(self) -> bool:
        return self.status is PostStatus.APPROVED and self.deleted_at is None

    @property
    def is_anonymous(self) -> bool:
        return self.reporter_id is None

    def approve(self, now: datetime) -> None:
        self.status = PostStatus.APPROVED
        # Set once: re-approving after a hide must not shift the leaderboard bucket.
        if self.approved_at is None:
            self.approved_at = now

    def reject(self, now: datetime) -> None:
        self.status = PostStatus.REJECTED
        self.deleted_at = now

    def hide(self) -> None:
        self.status = PostStatus.HIDDEN

    def unhide(self, now: datetime) -> None:
        self.approve(now)


@dataclass
class Engagement:
    id: EngagementId | None
    post_id: PostId
    type: EngagementType
    actor_id: UserId | None  # None => anonymous
    body: str | None = None  # comments only
    created: datetime | None = None

    @property
    def is_anonymous(self) -> bool:
        return self.actor_id is None


@dataclass
class PointRule:
    code: str
    points: int
    active: bool = True
    description: str = ""

    @property
    def effective_points(self) -> int:
        return self.points if self.active else 0


@dataclass
class LevelRule:
    level: int
    min_points: int
    title: str


@dataclass
class Feedback:
    """The "rate us" submission. Never displayed publicly."""

    id: FeedbackId | None
    user_id: UserId | None
    name: str
    email: str
    rating: int  # 1..5
    comment: str
    created: datetime | None = None


@dataclass
class ContactMessage:
    id: ContactMessageId | None
    user_id: UserId | None
    name: str
    email: str
    phone: str
    subject: str
    message: str
    status: str = "new"  # new | read | replied
    created: datetime | None = None


@dataclass
class ContactPage:
    """Singleton. Admin-editable content for the public contact page."""

    heading: str = ""
    intro: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    map_point: GeoPoint | None = None
    socials: list[SocialLink] = field(default_factory=list)
    updated_at: datetime | None = None
    updated_by: UserId | None = None


@dataclass
class PostModerationLog:
    """Audit trail for humans. NEVER an input to point calculation (LLD DEC-4)."""

    id: ModerationLogId | None
    post_id: PostId
    admin_id: UserId
    action: ModerationAction
    reason: str
    at: datetime
