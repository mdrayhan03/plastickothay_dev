"""Integration-test fixtures."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _seed_rules(db):
    """Point and level rules are read from the DB by the scoring endpoints. Seed them so the
    leaderboard/contribution tests see the real scheme (mirrors `manage.py seed_rules`)."""
    from adapters.persistence.django_orm import models as orm
    from adapters.persistence.django_orm.management.commands.seed_rules import (
        BADGE_RULES,
        LEVEL_RULES,
        POINT_RULES,
    )

    for code, points, active, desc in POINT_RULES:
        orm.PointRule.objects.update_or_create(
            code=code, defaults={"points": points, "active": active, "description": desc}
        )
    for level, min_points, title in LEVEL_RULES:
        orm.LevelRule.objects.update_or_create(
            level=level, defaults={"min_points": min_points, "title": title}
        )
    for code, name, desc, criteria, threshold, active, icon in BADGE_RULES:
        orm.BadgeRule.objects.update_or_create(
            code=code,
            defaults={"name": name, "description": desc, "criteria": criteria,
                      "threshold": threshold, "active": active, "icon": icon},
        )


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Throttle counters live in the cache and would otherwise leak between tests — one test's
    submissions would exhaust another's rate limit. Dedicated throttle tests clear and drive
    the limit explicitly."""
    cache.clear()
    yield
    cache.clear()
