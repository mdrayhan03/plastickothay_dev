"""Seed point rules and level rules.

Idempotent: safe to re-run. Values mirror tests/fakes/seed.py so the fake and the real DB
start from the same scheme.

NOTE: the level thresholds are a PLACEHOLDER pending a product decision (B0 report §6.1). The
legacy "every 5 points = 1 level" is meaningless now one approved post is worth 100.
"""

from django.core.management.base import BaseCommand

from adapters.persistence.django_orm import models as orm

POINT_RULES = [
    ("post_approved", 100, True, "Your report was approved."),
    ("like_received", 3, True, "Someone liked your approved report."),
    ("like_given", 1, True, "You liked someone else's approved report."),
    ("comment_received", 0, False, "A comment on your report (v2)."),
    ("comment_given", 0, False, "You commented on a report (v2)."),
]

LEVEL_RULES = [
    (1, 0, "Newcomer"),
    (2, 100, "Reporter"),
    (3, 300, "Contributor"),
    (4, 700, "Guardian"),
    (5, 1500, "Champion"),
]

# (code, name, description, criteria, threshold, active, icon)
BADGE_RULES = [
    ("first_report", "First Report", "Got your first report approved.", "posts_approved", 1, True, "🌱"),  # noqa: E501
    ("reporter_10", "Active Reporter", "10 approved reports.", "posts_approved", 10, True, "📸"),
    ("reporter_50", "Dedicated Reporter", "50 approved reports.", "posts_approved", 50, True, "🏅"),  # noqa: E501
    ("well_liked", "Well Liked", "Received 25 likes.", "likes_received", 25, True, "❤️"),
    ("supporter", "Supporter", "Gave 25 likes to others.", "likes_given", 25, True, "🤝"),
    ("champion", "Champion", "Reached 1500 points.", "points_total", 1500, True, "👑"),
]


class Command(BaseCommand):
    help = "Seed point/level/badge rules and site config. Create-if-missing: safe to re-run, "
    help += "and it never overwrites values an admin has since changed in the database."

    def handle(self, *args, **options):
        # get_or_create, NOT update_or_create: these values start from code defaults but the
        # DATABASE is the source of truth once seeded — admins edit them at runtime. Re-running
        # (e.g. on every deploy) must only create rows that don't exist yet, never reset an
        # admin's change back to the code default. A NEW rule added to the lists below gets
        # created on the next run; existing rows are left untouched. Changing a shipped default
        # in code is therefore a deliberate admin/data action, not an automatic seed overwrite.
        for code, points, active, desc in POINT_RULES:
            orm.PointRule.objects.get_or_create(
                code=code,
                defaults={"points": points, "active": active, "description": desc},
            )
        for level, min_points, title in LEVEL_RULES:
            orm.LevelRule.objects.get_or_create(
                level=level, defaults={"min_points": min_points, "title": title}
            )
        for code, name, desc, criteria, threshold, active, icon in BADGE_RULES:
            orm.BadgeRule.objects.get_or_create(
                code=code,
                defaults={
                    "name": name, "description": desc, "criteria": criteria,
                    "threshold": threshold, "active": active, "icon": icon,
                },
            )
        # Ensure the SiteConfig singleton exists with defaults (Dhaka centre, Monday weeks).
        orm.SiteConfig.objects.get_or_create(
            pk=1,
            defaults={
                "week_start": "monday",
                "site_name": "PlasticKothay",
                "map_lat": 23.8103,
                "map_lon": 90.4125,
                "map_zoom": 12,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(POINT_RULES)} point rules, {len(LEVEL_RULES)} level rules, "
                f"{len(BADGE_RULES)} badge rules, and the site config."
            )
        )
