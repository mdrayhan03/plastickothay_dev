"""ORM models — a persistence detail, not the domain.

These are Active Record (they carry .save(), .objects). The domain never sees them: mappers.py
translates between these and the pure dataclasses in core.domain.entities. If a use case ever
imports this module, the DB port has become fiction (LLD §2.2).

Field choices mirror core.domain.value_objects; the integer codes are duplicated here rather
than imported so this module stays a leaf with no dependency back into core.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    """Custom user (DEC-5). AUTH_USER_MODEL points here; set before the first migration.

    Role maps to Django flags in the mapper: superuser=ADMIN, staff=STAFF, neither=USER.
    is_verified (completed OTP) is kept distinct from is_active (not banned) — the legacy
    model conflated them (LLD §9.1).
    """

    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "app_user"


class OTP(models.Model):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"
    PURPOSE_CHOICES = [(REGISTRATION, "Registration"), (PASSWORD_RESET, "Password reset")]

    username = models.CharField(max_length=150, db_index=True)
    code = models.IntegerField()
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "otp"
        indexes = [
            models.Index(fields=["username", "purpose", "expires_at"]),
            models.Index(fields=["expires_at"]),  # for purge_expired
        ]


class Post(models.Model):
    # Contact block — always present (anonymous submissions supply it directly).
    reporter_name = models.CharField(max_length=255)
    reporter_email = models.EmailField()
    reporter_phone = models.CharField(max_length=20)
    # Set only for authenticated submissions.
    reporter_user = models.ForeignKey(
        "User", null=True, blank=True, on_delete=models.SET_NULL, related_name="posts"
    )

    severity = models.IntegerField()  # 1..5
    image_provider = models.CharField(max_length=32, default="gdrive")
    image_external_id = models.CharField(max_length=255)
    lat = models.FloatField()
    lon = models.FloatField()
    description = models.TextField(default="No description provided.")
    status = models.IntegerField(default=2)  # 0 reject, 1 approve, 2 pending, 3 hidden
    created = models.DateTimeField()
    approved_at = models.DateTimeField(null=True, blank=True)  # first approval; drives periods
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete

    class Meta:
        db_table = "post"
        indexes = [
            models.Index(fields=["status", "-created"]),  # public feed
            models.Index(fields=["status", "approved_at"]),  # leaderboard periods
            models.Index(fields=["reporter_user", "status"]),  # contribution
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(severity__gte=1) & Q(severity__lte=5), name="post_severity_range"
            ),
            models.CheckConstraint(
                condition=Q(lat__gte=-90) & Q(lat__lte=90), name="post_lat_range"
            ),
            models.CheckConstraint(
                condition=Q(lon__gte=-180) & Q(lon__lte=180), name="post_lon_range"
            ),
        ]


class Engagement(models.Model):
    LIKE = "like"
    COMMENT = "comment"
    TYPE_CHOICES = [(LIKE, "Like"), (COMMENT, "Comment")]

    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="engagements")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    actor_user = models.ForeignKey(
        "User", null=True, blank=True, on_delete=models.CASCADE, related_name="engagements"
    )
    # Denormalised so leaderboard SQL filters on the post owner without a self-join. Immutable.
    post_owner_user = models.ForeignKey(
        "User", null=True, blank=True, on_delete=models.CASCADE, related_name="+"
    )
    body = models.TextField(null=True, blank=True)  # comments only
    created = models.DateTimeField()

    class Meta:
        db_table = "engagement"
        constraints = [
            # ONE LIKE PER USER PER POST. Partial, so comments (later) stay unconstrained and
            # anonymous likes (actor_user IS NULL) are not bound — nothing identifies them,
            # which is exactly why they earn no points (DEC-1, LLD §9.3).
            models.UniqueConstraint(
                fields=["post", "actor_user"],
                condition=Q(type="like") & Q(actor_user__isnull=False),
                name="uniq_like_per_user_per_post",
            ),
        ]
        indexes = [
            models.Index(fields=["post", "type"]),
            models.Index(fields=["actor_user", "type"]),
            models.Index(fields=["created"]),
        ]


class PointRule(models.Model):
    code = models.CharField(max_length=64, unique=True)
    points = models.IntegerField()
    active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "point_rule"


class LevelRule(models.Model):
    level = models.IntegerField(unique=True)
    min_points = models.IntegerField()
    title = models.CharField(max_length=64)

    class Meta:
        db_table = "level_rule"
        ordering = ["min_points"]


class Feedback(models.Model):
    user = models.ForeignKey(
        "User", null=True, blank=True, on_delete=models.SET_NULL, related_name="feedback"
    )
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    rating = models.IntegerField()  # 1..5
    comment = models.TextField(blank=True)
    created = models.DateTimeField()

    class Meta:
        db_table = "feedback"
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5), name="feedback_rating_range"
            ),
        ]


class ContactPage(models.Model):
    """Singleton — enforced by pinning the primary key to 1."""

    id = models.IntegerField(primary_key=True, default=1)
    heading = models.CharField(max_length=255, blank=True)
    intro = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=512, blank=True)
    map_lat = models.FloatField(null=True, blank=True)
    map_lon = models.FloatField(null=True, blank=True)
    socials = models.JSONField(default=list)  # [{platform, url, order}] — small, bounded list
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        "User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "contact_page"
        constraints = [models.CheckConstraint(condition=Q(id=1), name="contact_page_singleton")]


class ContactMessage(models.Model):
    user = models.ForeignKey(
        "User", null=True, blank=True, on_delete=models.SET_NULL, related_name="contact_messages"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=16, default="new")  # new | read | replied
    created = models.DateTimeField()

    class Meta:
        db_table = "contact_message"
        indexes = [models.Index(fields=["status", "-created"])]


class PostModerationLog(models.Model):
    """Audit trail for humans. NEVER an input to point calculation (DEC-4)."""

    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="moderation_log")
    admin = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="+")
    action = models.CharField(max_length=16)  # approve | reject | hide | unhide
    reason = models.TextField(blank=True)
    at = models.DateTimeField()

    class Meta:
        db_table = "post_moderation_log"
        indexes = [models.Index(fields=["post", "at"])]
