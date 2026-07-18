"""Leaderboard calculation — the LeaderboardRepository strategy.

Implemented with the Django ORM rather than raw SQL so it runs on any backend (SQLite in
tests, Postgres in prod) and stays portable. The point rules live in TWO places now — the
reference implementation in core.domain.points (used by the fake) and this aggregation — so
they can drift. tests/contract/ runs identical scenarios against both; this implementation is
only "done" when it matches the reference there.

The escape hatch, if this is ever too slow: a MATERIALIZED VIEW behind the same port, with no
change above it. Do not pre-optimise.
"""

from __future__ import annotations

from datetime import datetime

from django.db.models import Count, F

from adapters.persistence.django_orm import models as orm
from core.domain.pagination import Page, PageRequest
from core.domain.periods import period_start
from core.domain.points import (
    RULE_LIKE_GIVEN,
    RULE_LIKE_RECEIVED,
    RULE_POST_APPROVED,
    Rules,
    level_for,
    level_progress,
)
from core.domain.read_models import Contribution, LeaderboardRow
from core.domain.value_objects import EngagementType, Period, PostStatus
from core.ports.repositories import LeaderboardRepository

APPROVED = int(PostStatus.APPROVED)


class _Row:
    __slots__ = ("posts_approved", "likes_received", "likes_given", "points")

    def __init__(self):
        self.posts_approved = 0
        self.likes_received = 0
        self.likes_given = 0
        self.points = 0


class DjangoLeaderboardRepository(LeaderboardRepository):
    def _compute(self, since: datetime | None, rules: Rules) -> dict[int, _Row]:
        acc: dict[int, _Row] = {}

        def row(uid: int) -> _Row:
            return acc.setdefault(uid, _Row())

        # --- approved posts → owner ---------------------------------------
        posts = orm.Post.objects.filter(
            status=APPROVED, deleted_at__isnull=True, reporter_user__isnull=False
        )
        if since is not None:
            posts = posts.filter(approved_at__gte=since)
        for r in posts.values("reporter_user_id").annotate(n=Count("pk")):
            entry = row(r["reporter_user_id"])
            entry.posts_approved += r["n"]
            entry.points += r["n"] * rules.get(RULE_POST_APPROVED, 0)

        # --- likes on approved posts (authenticated, non-self) ------------
        likes = orm.Engagement.objects.filter(
            type=EngagementType.LIKE.value,
            actor_user__isnull=False,
            post__status=APPROVED,
            post__deleted_at__isnull=True,
            post__reporter_user__isnull=False,
        ).exclude(actor_user_id=F("post__reporter_user_id"))
        if since is not None:
            likes = likes.filter(created__gte=since)

        for r in likes.values("post__reporter_user_id").annotate(n=Count("pk")):
            entry = row(r["post__reporter_user_id"])
            entry.likes_received += r["n"]
            entry.points += r["n"] * rules.get(RULE_LIKE_RECEIVED, 0)

        for r in likes.values("actor_user_id").annotate(n=Count("pk")):
            entry = row(r["actor_user_id"])
            entry.likes_given += r["n"]
            entry.points += r["n"] * rules.get(RULE_LIKE_GIVEN, 0)

        return acc

    def top(self, period: Period, rules: Rules, page: PageRequest) -> Page[LeaderboardRow]:
        # period_start needs a "now"; SystemClock isn't injected here, so use tz-aware now.
        from datetime import UTC
        from datetime import datetime as _dt

        since = period_start(period, _dt.now(UTC))
        scored = self._compute(since, rules)

        user_ids = [uid for uid, r in scored.items() if r.points > 0]
        users = {
            u.pk: u
            for u in orm.User.objects.filter(pk__in=user_ids).only(
                "pk", "username", "first_name", "last_name", "date_joined"
            )
        }
        ranked = sorted(
            (u for uid, u in users.items()),
            key=lambda u: (-scored[u.pk].points, u.date_joined, u.pk),
        )

        start = int(page.cursor) if page.cursor else 0
        window = ranked[start : start + page.limit]
        rows = [
            LeaderboardRow(
                user_id=u.pk,
                username=u.username,
                full_name=f"{u.first_name} {u.last_name}".strip(),
                points=scored[u.pk].points,
                rank=start + i + 1,
            )
            for i, u in enumerate(window)
        ]
        next_cursor = str(start + page.limit) if start + page.limit < len(ranked) else None
        return Page(items=rows, next_cursor=next_cursor)

    def contribution_for(self, user_id, rules, levels) -> Contribution:
        entry = self._compute(None, rules).get(user_id, _Row())
        current = level_for(entry.points, levels)
        to_next, progress = level_progress(entry.points, levels)
        return Contribution(
            user_id=user_id,
            total_points=entry.points,
            posts_approved=entry.posts_approved,
            likes_received=entry.likes_received,
            likes_given=entry.likes_given,
            level=current.level,
            level_title=current.title,
            points_to_next_level=to_next,
            progress_percentage=progress,
        )
