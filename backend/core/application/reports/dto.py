"""Commands for the reports use cases.

Plain dataclasses, not DRF serializers: the domain must not know DRF exists. Serializers at
the HTTP edge build these.
"""

from dataclasses import dataclass

from core.domain.ids import PostId, UserId


@dataclass(frozen=True, slots=True)
class SubmitReportCommand:
    severity: int
    lat: float
    lon: float
    photo_bytes: bytes  # already decoded — base64 is transport, handled at the edge
    filename: str
    content_type: str
    description: str = ""
    place_name: str = ""
    # Only used for anonymous submissions; ignored when the caller is authenticated.
    name: str = ""
    email: str = ""
    phone: str = ""


@dataclass(frozen=True, slots=True)
class UpdateDescriptionCommand:
    post_id: PostId
    description: str
    actor_id: UserId


@dataclass(frozen=True, slots=True)
class ModerateCommand:
    post_id: PostId
    admin_id: UserId
    reason: str = ""
