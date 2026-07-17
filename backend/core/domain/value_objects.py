"""Value objects — immutable, self-validating, no identity.

Replaces the magic numbers in the legacy code (``status=1``, ``user_type=3``).
"""

from dataclasses import dataclass
from enum import IntEnum, StrEnum

from core.domain.errors import InvalidLocation


class Severity(IntEnum):
    LOW = 1
    MINOR = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


class PostStatus(IntEnum):
    REJECTED = 0  # refused; image deleted from storage; soft-deleted
    APPROVED = 1  # public; earns points
    PENDING = 2  # awaiting review; not public; no points
    HIDDEN = 3  # was approved, taken down; not public; no points; image retained


class EngagementType(StrEnum):
    LIKE = "like"
    COMMENT = "comment"  # modelled for v2; rules seeded inactive


class Role(StrEnum):
    USER = "user"
    STAFF = "staff"
    ADMIN = "admin"

    @property
    def is_moderator(self) -> bool:
        return self in (Role.STAFF, Role.ADMIN)


class OTPPurpose(StrEnum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"


class Period(StrEnum):
    ALL = "all"
    YEAR = "year"
    MONTH = "month"
    WEEK = "week"


class ModerationAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    HIDE = "hide"
    UNHIDE = "unhide"


@dataclass(frozen=True, slots=True)
class Reporter:
    """Who to contact about a report. Always present, even for anonymous submissions."""

    name: str
    email: str
    phone: str


@dataclass(frozen=True, slots=True)
class GeoPoint:
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not -90 <= self.lat <= 90:
            raise InvalidLocation(f"Latitude {self.lat} is outside -90..90.", lat=self.lat)
        if not -180 <= self.lon <= 180:
            raise InvalidLocation(f"Longitude {self.lon} is outside -180..180.", lon=self.lon)


@dataclass(frozen=True, slots=True)
class ImageRef:
    provider: str  # "gdrive"
    external_id: str


@dataclass(frozen=True, slots=True)
class SocialLink:
    platform: str
    url: str
    order: int = 0
