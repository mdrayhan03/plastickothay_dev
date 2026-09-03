"""Django ORM implementations of the repository ports.

The only module (besides mappers) that touches ORM objects. Everything returned is a domain
entity or read model; nothing that leaves here is a model instance or a QuerySet.

`def list()` shadows the builtin inside class bodies, so annotations are deferred.
"""

from __future__ import annotations

import base64
from datetime import datetime

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek

from adapters.persistence.django_orm import mappers
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
    User,
)
from core.domain.errors import (
    AlreadyLiked,
    EmailTaken,
    UsernameTaken,
    UserNotFound,
)
from core.domain.ids import ContactMessageId, PostId, UserId
from core.domain.pagination import Page, PageRequest
from core.domain.points import Rules
from core.domain.read_models import (
    AdminMapMarker,
    MapMarker,
    PostAnalytics,
    PostFilter,
    StatusCounts,
    WeeklyPoint,
)
from core.domain.value_objects import EngagementType, OTPPurpose, PostStatus, Role
from core.ports.repositories import (
    BadgeRepository,
    ContactRepository,
    EngagementRepository,
    FeedbackRepository,
    LevelRuleRepository,
    ModerationLogRepository,
    OTPRepository,
    PointRuleRepository,
    PostRepository,
    SiteConfigRepository,
    UserRepository,
)

# --- cursor helpers --------------------------------------------------------
# Keyset over (created DESC, id DESC): stable under inserts, unlike offset pagination.


def _encode_cursor(created: datetime, pk: int) -> str:
    raw = f"{created.isoformat()}|{pk}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, int]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    created_iso, pk = raw.rsplit("|", 1)
    return datetime.fromisoformat(created_iso), int(pk)


def _keyset_page(queryset, page: PageRequest, to_domain) -> Page:
    """Paginate a queryset already ordered by (-created, -id)."""
    if page.cursor:
        created, pk = _decode_cursor(page.cursor)
        queryset = queryset.filter(Q(created__lt=created) | Q(created=created, pk__lt=pk))
    rows = list(queryset[: page.limit + 1])
    has_next = len(rows) > page.limit
    rows = rows[: page.limit]
    next_cursor = _encode_cursor(rows[-1].created, rows[-1].pk) if has_next and rows else None
    return Page(items=[to_domain(r) for r in rows], next_cursor=next_cursor)


class DjangoUserRepository(UserRepository):
    def get(self, id: UserId) -> User | None:
        row = orm.User.objects.filter(pk=id).first()
        return mappers.user_to_domain(row) if row else None

    def get_by_username(self, username: str) -> User | None:
        row = orm.User.objects.filter(username=username).first()
        return mappers.user_to_domain(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = orm.User.objects.filter(email=email).first()
        return mappers.user_to_domain(row) if row else None

    def add(self, user: User, password: str) -> User:
        is_superuser, is_staff = mappers.flags_from_role(user.role)
        try:
            # Savepoint: a caught IntegrityError otherwise poisons the surrounding
            # transaction, so any query after the except (in the same request) would raise
            # TransactionManagementError.
            with transaction.atomic():
                row = orm.User.objects.create(
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone=user.phone,
                    password=make_password(password),
                    is_superuser=is_superuser,
                    is_staff=is_staff,
                    is_verified=user.is_verified,
                    is_active=user.is_active,
                    avatar_provider=user.avatar.provider if user.avatar else "",
                    avatar_external_id=user.avatar.external_id if user.avatar else "",
                    date_joined=user.date_joined,
                )
        except IntegrityError as exc:
            # Translate the DB's unique violation rather than pre-checking: a check-then-act
            # would race under concurrent registration.
            if "email" in str(exc).lower():
                raise EmailTaken() from exc
            raise UsernameTaken() from exc
        return mappers.user_to_domain(row)

    def update(self, user: User) -> User:
        row = orm.User.objects.filter(pk=user.id).first()
        if row is None:
            raise UserNotFound()
        is_superuser, is_staff = mappers.flags_from_role(user.role)
        row.username = user.username
        row.email = user.email
        row.first_name = user.first_name
        row.last_name = user.last_name
        row.phone = user.phone
        row.is_superuser = is_superuser
        row.is_staff = is_staff
        row.is_verified = user.is_verified
        row.is_active = user.is_active
        row.avatar_provider = user.avatar.provider if user.avatar else ""
        row.avatar_external_id = user.avatar.external_id if user.avatar else ""
        row.save()
        return mappers.user_to_domain(row)

    def set_password(self, id: UserId, password: str) -> None:
        row = orm.User.objects.filter(pk=id).first()
        if row is None:
            raise UserNotFound()
        row.password = make_password(password)
        row.save(update_fields=["password"])

    def verify_password(self, id: UserId, password: str) -> bool:
        row = orm.User.objects.filter(pk=id).first()
        return bool(row and check_password(password, row.password))

    def set_role(self, id: UserId, role: Role) -> User:
        row = orm.User.objects.filter(pk=id).first()
        if row is None:
            raise UserNotFound()
        row.is_superuser, row.is_staff = mappers.flags_from_role(role)
        row.save(update_fields=["is_superuser", "is_staff"])
        return mappers.user_to_domain(row)

    def set_active(self, id: UserId, is_active: bool) -> User:
        row = orm.User.objects.filter(pk=id).first()
        if row is None:
            raise UserNotFound()
        row.is_active = is_active
        row.save(update_fields=["is_active"])
        return mappers.user_to_domain(row)

    def delete(self, id: UserId) -> None:
        # Posts' reporter_user is SET_NULL, so their reports survive (anonymised).
        orm.User.objects.filter(pk=id).delete()

    def touch_last_login(self, id: UserId, at: datetime) -> None:
        orm.User.objects.filter(pk=id).update(last_login=at)

    def list(self, page: PageRequest) -> Page[User]:
        start = int(page.cursor) if page.cursor else 0
        qs = orm.User.objects.order_by("pk")
        rows = list(qs[start : start + page.limit + 1])
        has_next = len(rows) > page.limit
        rows = rows[: page.limit]
        next_cursor = str(start + page.limit) if has_next else None
        return Page(items=[mappers.user_to_domain(r) for r in rows], next_cursor=next_cursor)


class DjangoOTPRepository(OTPRepository):
    def add(self, otp: OTP) -> OTP:
        row = orm.OTP.objects.create(
            username=otp.username,
            code=otp.code,
            purpose=otp.purpose.value,
            created_at=otp.created_at,
            expires_at=otp.expires_at,
        )
        return mappers.otp_to_domain(row)

    def latest_valid_for(self, username: str, purpose: OTPPurpose, now: datetime) -> OTP | None:
        row = (
            orm.OTP.objects.filter(username=username, purpose=purpose.value, expires_at__gt=now)
            .order_by("-created_at")
            .first()
        )
        return mappers.otp_to_domain(row) if row else None

    def invalidate_for(self, username: str, purpose: OTPPurpose) -> None:
        orm.OTP.objects.filter(username=username, purpose=purpose.value).delete()

    def purge_expired(self, now: datetime) -> int:
        deleted, _ = orm.OTP.objects.filter(expires_at__lte=now).delete()
        return deleted


class DjangoPostRepository(PostRepository):
    def get(self, id: PostId) -> Post | None:
        row = orm.Post.objects.filter(pk=id).first()
        return mappers.post_to_domain(row) if row else None

    def add(self, post: Post) -> Post:
        row = mappers.post_apply_to_orm(post, orm.Post())
        row.save()
        return mappers.post_to_domain(row)

    def update(self, post: Post) -> Post:
        row = orm.Post.objects.filter(pk=post.id).first()
        if row is None:
            from core.domain.errors import PostNotFound

            raise PostNotFound()
        mappers.post_apply_to_orm(post, row)
        row.save()
        return mappers.post_to_domain(row)

    def list(self, filter: PostFilter, page: PageRequest) -> Page[Post]:
        qs = orm.Post.objects.filter(status__in=[int(s) for s in filter.statuses])
        if not filter.include_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        if filter.severity is not None:
            qs = qs.filter(severity=int(filter.severity))
        if filter.reporter_id is not None:
            qs = qs.filter(reporter_user_id=filter.reporter_id)
        if filter.created_after is not None:
            qs = qs.filter(created__gte=filter.created_after)
        if filter.created_before is not None:
            qs = qs.filter(created__lte=filter.created_before)
        qs = qs.order_by("-created", "-pk")
        return _keyset_page(qs, page, mappers.post_to_domain)

    def list_map_markers(self) -> list[MapMarker]:
        rows = orm.Post.objects.filter(
            status=int(PostStatus.APPROVED), deleted_at__isnull=True
        ).values("pk", "lat", "lon", "severity", "image_provider", "image_external_id")
        from core.domain.value_objects import ImageRef, Severity

        return [
            MapMarker(
                id=PostId(r["pk"]),
                lat=r["lat"],
                lon=r["lon"],
                severity=Severity(r["severity"]),
                image=ImageRef(provider=r["image_provider"], external_id=r["image_external_id"])
                if r.get("image_external_id")
                else None,
            )
            for r in rows
        ]

    def list_admin_map_markers(self) -> list[AdminMapMarker]:
        from core.domain.value_objects import ImageRef, Severity

        rows = orm.Post.objects.filter(deleted_at__isnull=True).values(
            "pk", "lat", "lon", "severity", "status", "image_provider", "image_external_id"
        )
        return [
            AdminMapMarker(
                id=PostId(r["pk"]),
                lat=r["lat"],
                lon=r["lon"],
                severity=Severity(r["severity"]),
                status=PostStatus(r["status"]),
                image=ImageRef(provider=r["image_provider"], external_id=r["image_external_id"])
                if r.get("image_external_id")
                else None,
            )
            for r in rows
        ]

    def counts_by_status(self) -> StatusCounts:
        rows = (
            orm.Post.objects.filter(deleted_at__isnull=True)
            .values("status")
            .annotate(n=Count("pk"))
        )
        counts = {PostStatus(r["status"]): r["n"] for r in rows}
        # Rejected posts are soft-deleted, so count them separately.
        rejected = orm.Post.objects.filter(status=int(PostStatus.REJECTED)).count()
        if rejected:
            counts[PostStatus.REJECTED] = rejected
        return StatusCounts(counts=counts)

    def analytics(self, since: datetime) -> PostAnalytics:
        submitted = {
            r["w"].date(): r["n"]
            for r in orm.Post.objects.filter(created__gte=since)
            .annotate(w=TruncWeek("created"))
            .values("w")
            .annotate(n=Count("pk"))
        }
        approved = {
            r["w"].date(): r["n"]
            for r in orm.Post.objects.filter(approved_at__gte=since)
            .annotate(w=TruncWeek("approved_at"))
            .values("w")
            .annotate(n=Count("pk"))
        }
        over_time = [
            WeeklyPoint(week=w, submitted=submitted.get(w, 0), approved=approved.get(w, 0))
            for w in sorted(set(submitted) | set(approved))
        ]
        active_users = (
            orm.Post.objects.filter(created__gte=since, reporter_user__isnull=False)
            .values("reporter_user")
            .distinct()
            .count()
        )
        return PostAnalytics(over_time=over_time, active_users=active_users)


class DjangoEngagementRepository(EngagementRepository):
    def add(self, engagement: Engagement) -> Engagement:
        owner_id = self._owner_of(engagement.post_id)
        try:
            # Savepoint so the caught IntegrityError does not poison the request's outer
            # transaction - LikePost reads count() right after catching AlreadyLiked.
            with transaction.atomic():
                row = orm.Engagement.objects.create(
                    post_id=engagement.post_id,
                    type=engagement.type.value,
                    actor_user_id=engagement.actor_id,
                    post_owner_user_id=owner_id,
                    body=engagement.body,
                    created=engagement.created,
                )
        except IntegrityError as exc:
            # The partial unique index is the guard, not a pre-check (LLD §7.2).
            raise AlreadyLiked() from exc
        return mappers.engagement_to_domain(row)

    def _owner_of(self, post_id: PostId) -> int | None:
        return (
            orm.Post.objects.filter(pk=post_id).values_list("reporter_user_id", flat=True).first()
        )

    def get_like(self, post_id: PostId, actor_id: UserId) -> Engagement | None:
        row = orm.Engagement.objects.filter(
            post_id=post_id, actor_user_id=actor_id, type=EngagementType.LIKE.value
        ).first()
        return mappers.engagement_to_domain(row) if row else None

    def remove_like(self, post_id: PostId, actor_id: UserId) -> bool:
        deleted, _ = orm.Engagement.objects.filter(
            post_id=post_id, actor_user_id=actor_id, type=EngagementType.LIKE.value
        ).delete()
        return deleted > 0

    def count(self, post_id: PostId, type: EngagementType) -> int:
        return orm.Engagement.objects.filter(post_id=post_id, type=type.value).count()

    def counts_for(self, post_ids: list[PostId], type: EngagementType) -> dict[PostId, int]:
        rows = (
            orm.Engagement.objects.filter(post_id__in=post_ids, type=type.value)
            .values("post_id")
            .annotate(n=Count("pk"))
        )
        return {PostId(r["post_id"]): r["n"] for r in rows}

    def liked_post_ids(self, post_ids: list[PostId], actor_id: UserId) -> set[PostId]:
        rows = orm.Engagement.objects.filter(
            post_id__in=post_ids, actor_user_id=actor_id, type=EngagementType.LIKE.value
        ).values_list("post_id", flat=True)
        return {PostId(pk) for pk in rows}


class DjangoPointRuleRepository(PointRuleRepository):
    def active_rules(self) -> Rules:
        # Inactive rules resolve to 0, not absent, so the calculator never KeyErrors.
        return {r.code: (r.points if r.active else 0) for r in orm.PointRule.objects.all()}


class DjangoLevelRuleRepository(LevelRuleRepository):
    def all(self) -> list[LevelRule]:
        return [
            mappers.level_rule_to_domain(r) for r in orm.LevelRule.objects.order_by("min_points")
        ]


class DjangoFeedbackRepository(FeedbackRepository):
    def add(self, feedback: Feedback) -> Feedback:
        row = orm.Feedback.objects.create(
            user_id=feedback.user_id,
            name=feedback.name,
            email=feedback.email,
            rating=feedback.rating,
            comment=feedback.comment,
            created=feedback.created,
        )
        return mappers.feedback_to_domain(row)

    def list(self, page: PageRequest) -> Page[Feedback]:
        qs = orm.Feedback.objects.order_by("-created", "-pk")
        return _keyset_page(qs, page, mappers.feedback_to_domain)


class DjangoContactRepository(ContactRepository):
    def get_page(self) -> ContactPage:
        row, _ = orm.ContactPage.objects.get_or_create(pk=1)
        return mappers.contact_page_to_domain(row)

    def save_page(self, page: ContactPage) -> ContactPage:
        row, _ = orm.ContactPage.objects.get_or_create(pk=1)
        row.heading = page.heading
        row.intro = page.intro
        row.email = page.email
        row.phone = page.phone
        row.address = page.address
        row.map_lat = page.map_point.lat if page.map_point else None
        row.map_lon = page.map_point.lon if page.map_point else None
        row.socials = [
            {"platform": s.platform, "url": s.url, "order": s.order} for s in page.socials
        ]
        row.updated_at = page.updated_at
        row.updated_by_id = page.updated_by
        row.save()
        return mappers.contact_page_to_domain(row)

    def add_message(self, message: ContactMessage) -> ContactMessage:
        row = orm.ContactMessage.objects.create(
            user_id=message.user_id,
            name=message.name,
            email=message.email,
            phone=message.phone,
            subject=message.subject,
            message=message.message,
            status=message.status,
            created=message.created,
        )
        return mappers.contact_message_to_domain(row)

    def get_message(self, id: ContactMessageId) -> ContactMessage | None:
        row = orm.ContactMessage.objects.filter(pk=id).first()
        return mappers.contact_message_to_domain(row) if row else None

    def update_message(self, message: ContactMessage) -> ContactMessage:
        row = orm.ContactMessage.objects.filter(pk=message.id).first()
        row.status = message.status
        row.save(update_fields=["status"])
        return mappers.contact_message_to_domain(row)

    def list_messages(self, page: PageRequest) -> Page[ContactMessage]:
        qs = orm.ContactMessage.objects.order_by("-created", "-pk")
        return _keyset_page(qs, page, mappers.contact_message_to_domain)


class DjangoModerationLogRepository(ModerationLogRepository):
    def add(self, entry: PostModerationLog) -> PostModerationLog:
        row = orm.PostModerationLog.objects.create(
            post_id=entry.post_id,
            admin_id=entry.admin_id,
            action=entry.action.value,
            reason=entry.reason,
            at=entry.at,
        )
        return mappers.moderation_log_to_domain(row)

    def list_for_post(self, post_id: PostId) -> list[PostModerationLog]:
        return [
            mappers.moderation_log_to_domain(r)
            for r in orm.PostModerationLog.objects.filter(post_id=post_id).order_by("at")
        ]

    def list(self, page: PageRequest) -> Page[PostModerationLog]:
        start = int(page.cursor) if page.cursor else 0
        qs = orm.PostModerationLog.objects.order_by("-at", "-pk")
        rows = list(qs[start : start + page.limit + 1])
        has_next = len(rows) > page.limit
        rows = rows[: page.limit]
        next_cursor = str(start + page.limit) if has_next else None
        return Page(
            items=[mappers.moderation_log_to_domain(r) for r in rows], next_cursor=next_cursor
        )


class DjangoBadgeRepository(BadgeRepository):
    def active_rules(self):
        return [mappers.badge_rule_to_domain(r) for r in orm.BadgeRule.objects.filter(active=True)]

    def rules_by_code(self):
        return {r.code: mappers.badge_rule_to_domain(r) for r in orm.BadgeRule.objects.all()}

    def earned_codes(self, user_id: UserId) -> set[str]:
        return set(
            orm.UserBadge.objects.filter(user_id=user_id).values_list("badge_code", flat=True)
        )

    def award(self, user_id: UserId, code: str, at) -> None:
        # Idempotent: the unique(user, badge_code) constraint makes a repeat award a no-op.
        with transaction.atomic():
            orm.UserBadge.objects.get_or_create(
                user_id=user_id, badge_code=code, defaults={"earned_at": at}
            )

    def list_earned(self, user_id: UserId):
        return [
            mappers.user_badge_to_domain(r)
            for r in orm.UserBadge.objects.filter(user_id=user_id).order_by("earned_at")
        ]


class DjangoSiteConfigRepository(SiteConfigRepository):
    def get(self):
        row, _ = orm.SiteConfig.objects.get_or_create(pk=1)
        return mappers.site_config_to_domain(row)

    def save(self, config):
        row, _ = orm.SiteConfig.objects.get_or_create(pk=1)
        row.week_start = config.week_start.value
        row.site_name = config.site_name
        row.tagline = config.tagline
        row.logo_provider = config.logo.provider if config.logo else ""
        row.logo_external_id = config.logo.external_id if config.logo else ""
        row.map_lat = config.map_center.lat if config.map_center else None
        row.map_lon = config.map_center.lon if config.map_center else None
        row.map_zoom = config.map_zoom
        row.flags = dict(config.flags)
        row.updated_at = config.updated_at
        row.updated_by_id = config.updated_by
        row.save()
        return mappers.site_config_to_domain(row)
