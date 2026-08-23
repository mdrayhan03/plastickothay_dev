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

from adapters.persistence.django_orm import models as orm


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
        # Singleton - exactly one row, created via the API/get_or_create.
        return not orm.ContactPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
