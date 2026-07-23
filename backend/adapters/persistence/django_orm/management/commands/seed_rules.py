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


class Command(BaseCommand):
    help = "Seed point rules and level rules (idempotent)."

    def handle(self, *args, **options):
        for code, points, active, desc in POINT_RULES:
            orm.PointRule.objects.update_or_create(
                code=code,
                defaults={"points": points, "active": active, "description": desc},
            )
        for level, min_points, title in LEVEL_RULES:
            orm.LevelRule.objects.update_or_create(
                level=level, defaults={"min_points": min_points, "title": title}
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
                "and the site config."
            )
        )
