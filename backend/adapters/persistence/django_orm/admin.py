"""Django admin - CONFIG TABLES ONLY (LLD §11.4, DEC-9).

Registered: PointRule, LevelRule, ContactPage - data with no behaviour, edited rarely by
you. This is the stopgap until React admin exists.

DELIBERATELY NOT registered: Post, Engagement, User, Feedback, ContactMessage. Post especially
must never be here - approving a post has real behaviour (email, Drive deletion, points via
status) that lives in use cases, and the admin would write `status` directly and bypass all of
it. Everything with behaviour goes through the API. This restriction is the rule reviewers
enforce; adding a model here is a design decision, not a convenience.
"""

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session

from adapters.persistence.django_orm import models as orm



@admin.register(orm.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "phone", "is_verified", "is_staff", "is_superuser", "date_joined")
    list_filter = ("is_verified", "is_staff", "is_superuser")
    search_fields = ("username", "email", "phone")


@admin.register(orm.OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("username", "code", "purpose", "created_at", "expires_at")
    list_filter = ("purpose",)
    search_fields = ("username",)


@admin.register(orm.Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter_name", "reporter_email", "severity", "status", "created", "approved_at")
    list_filter = ("severity", "status")
    search_fields = ("reporter_name", "reporter_email", "description", "place_name")


@admin.register(orm.Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "type", "actor_user", "created")
    list_filter = ("type",)


@admin.register(orm.UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge_code", "earned_at")
    search_fields = ("user__username", "badge_code")


@admin.register(orm.Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "rating", "created")
    list_filter = ("rating",)
    search_fields = ("name", "email", "comment")


@admin.register(orm.ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "subject", "status", "created")
    list_filter = ("status",)
    search_fields = ("name", "email", "subject", "message")


@admin.register(orm.PointRule)
class PointRuleAdmin(admin.ModelAdmin):
    list_display = ("code", "points", "active", "description")
    list_editable = ("points", "active")


@admin.register(orm.LevelRule)
class LevelRuleAdmin(admin.ModelAdmin):
    list_display = ("level", "min_points", "title")
    list_editable = ("min_points", "title")
    ordering = ("min_points",)


@admin.register(orm.BadgeRule)
class BadgeRuleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "criteria", "threshold", "active", "icon")
    list_editable = ("threshold", "active")


@admin.register(orm.ContactPage)
class ContactPageAdmin(admin.ModelAdmin):
    list_display = ("heading", "email", "phone", "updated_at")

    def has_add_permission(self, request):
        return not orm.ContactPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(orm.SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ("site_name", "week_start", "updated_at")

    def has_add_permission(self, request):
        return not orm.SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(orm.PostModerationLog)
class PostModerationLogAdmin(admin.ModelAdmin):
    list_display = ("post", "admin", "action", "at")
    list_filter = ("action",)


# --- Django Built-in System Models ---

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "codename")
    list_filter = ("content_type",)
    search_fields = ("name", "codename")


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ("app_label", "model")
    list_filter = ("app_label",)
    search_fields = ("app_label", "model")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "expire_date")
    search_fields = ("session_key",)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("action_time", "user", "content_type", "object_repr", "action_flag")
    list_filter = ("action_flag", "content_type")
    search_fields = ("object_repr", "change_message")



