"""Translation between ORM rows and domain entities.

The only place ORM objects are touched apart from the repositories themselves. Everything
above the repository sees domain dataclasses, never a model instance and never a QuerySet.
"""

from adapters.persistence.django_orm import models as orm
from core.domain.entities import (
    OTP,
    ContactMessage,
    ContactPage,
    Engagement,
    Feedback,
    LevelRule,
    Post,
    PostModerationLog,
    SiteConfig,
    User,
)
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
    WeekStart,
)

# --- User ------------------------------------------------------------------
# Role is derived from Django's flags rather than stored (LLD §9.1): superuser => ADMIN,
# staff => STAFF, neither => USER. There is no separate role column.


def role_from_flags(is_superuser: bool, is_staff: bool) -> Role:
    if is_superuser:
        return Role.ADMIN
    if is_staff:
        return Role.STAFF
    return Role.USER


def flags_from_role(role: Role) -> tuple[bool, bool]:
    """Returns (is_superuser, is_staff)."""
    return role is Role.ADMIN, role in (Role.ADMIN, Role.STAFF)


def user_to_domain(row: orm.User) -> User:
    return User(
        id=UserId(row.pk),
        username=row.username,
        email=row.email,
        first_name=row.first_name,
        last_name=row.last_name,
        phone=row.phone,
        role=role_from_flags(row.is_superuser, row.is_staff),
        is_verified=row.is_verified,
        is_active=row.is_active,
        date_joined=row.date_joined,
        last_login=row.last_login,
    )


# --- OTP -------------------------------------------------------------------


def otp_to_domain(row: orm.OTP) -> OTP:
    return OTP(
        id=OTPId(row.pk),
        username=row.username,
        code=row.code,
        purpose=OTPPurpose(row.purpose),
        created_at=row.created_at,
        expires_at=row.expires_at,
    )


# --- Post ------------------------------------------------------------------


def post_to_domain(row: orm.Post) -> Post:
    return Post(
        id=PostId(row.pk),
        reporter=Reporter(
            name=row.reporter_name, email=row.reporter_email, phone=row.reporter_phone
        ),
        reporter_id=UserId(row.reporter_user_id) if row.reporter_user_id else None,
        severity=Severity(row.severity),
        image=ImageRef(provider=row.image_provider, external_id=row.image_external_id),
        location=GeoPoint(row.lat, row.lon),
        description=row.description,
        status=PostStatus(row.status),
        created=row.created,
        approved_at=row.approved_at,
        deleted_at=row.deleted_at,
    )


def post_apply_to_orm(entity: Post, row: orm.Post) -> orm.Post:
    """Copy a domain Post onto an ORM row (new or existing). Does not save."""
    row.reporter_name = entity.reporter.name
    row.reporter_email = entity.reporter.email
    row.reporter_phone = entity.reporter.phone
    row.reporter_user_id = entity.reporter_id
    row.severity = int(entity.severity)
    row.image_provider = entity.image.provider
    row.image_external_id = entity.image.external_id
    row.lat = entity.location.lat
    row.lon = entity.location.lon
    row.description = entity.description
    row.status = int(entity.status)
    row.created = entity.created
    row.approved_at = entity.approved_at
    row.deleted_at = entity.deleted_at
    return row


# --- Engagement ------------------------------------------------------------


def engagement_to_domain(row: orm.Engagement) -> Engagement:
    return Engagement(
        id=EngagementId(row.pk),
        post_id=PostId(row.post_id),
        type=EngagementType(row.type),
        actor_id=UserId(row.actor_user_id) if row.actor_user_id else None,
        body=row.body,
        created=row.created,
    )


# --- LevelRule -------------------------------------------------------------


def level_rule_to_domain(row: orm.LevelRule) -> LevelRule:
    return LevelRule(level=row.level, min_points=row.min_points, title=row.title)


# --- Feedback --------------------------------------------------------------


def feedback_to_domain(row: orm.Feedback) -> Feedback:
    return Feedback(
        id=FeedbackId(row.pk),
        user_id=UserId(row.user_id) if row.user_id else None,
        name=row.name,
        email=row.email,
        rating=row.rating,
        comment=row.comment,
        created=row.created,
    )


# --- ContactPage -----------------------------------------------------------


def contact_page_to_domain(row: orm.ContactPage) -> ContactPage:
    map_point = None
    if row.map_lat is not None and row.map_lon is not None:
        map_point = GeoPoint(row.map_lat, row.map_lon)
    return ContactPage(
        heading=row.heading,
        intro=row.intro,
        email=row.email,
        phone=row.phone,
        address=row.address,
        map_point=map_point,
        socials=[SocialLink(**s) for s in row.socials],
        updated_at=row.updated_at,
        updated_by=UserId(row.updated_by_id) if row.updated_by_id else None,
    )


# --- ContactMessage --------------------------------------------------------


def contact_message_to_domain(row: orm.ContactMessage) -> ContactMessage:
    return ContactMessage(
        id=ContactMessageId(row.pk),
        user_id=UserId(row.user_id) if row.user_id else None,
        name=row.name,
        email=row.email,
        phone=row.phone,
        subject=row.subject,
        message=row.message,
        status=row.status,
        created=row.created,
    )


# --- PostModerationLog -----------------------------------------------------


def site_config_to_domain(row: orm.SiteConfig) -> SiteConfig:
    logo = None
    if row.logo_external_id:
        logo = ImageRef(provider=row.logo_provider or "local", external_id=row.logo_external_id)
    map_center = None
    if row.map_lat is not None and row.map_lon is not None:
        map_center = GeoPoint(row.map_lat, row.map_lon)
    return SiteConfig(
        week_start=WeekStart(row.week_start),
        site_name=row.site_name,
        tagline=row.tagline,
        logo=logo,
        map_center=map_center,
        map_zoom=row.map_zoom,
        flags=dict(row.flags or {}),
        updated_at=row.updated_at,
        updated_by=UserId(row.updated_by_id) if row.updated_by_id else None,
    )


def moderation_log_to_domain(row: orm.PostModerationLog) -> PostModerationLog:
    return PostModerationLog(
        id=ModerationLogId(row.pk),
        post_id=PostId(row.post_id),
        admin_id=UserId(row.admin_id) if row.admin_id else None,
        action=ModerationAction(row.action),
        reason=row.reason,
        at=row.at,
    )
