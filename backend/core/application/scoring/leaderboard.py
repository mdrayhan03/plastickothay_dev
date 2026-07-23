"""Leaderboard and per-user contribution.

The period window (period → `since`) is computed HERE, in the domain/use-case, from the clock
and the admin-configured week-start (SiteConfig). The leaderboard repository only filters by
the resulting timestamp — no time, timezone, or period logic lives in the adapter.
"""

from core.domain.ids import UserId
from core.domain.pagination import Page, PageRequest
from core.domain.periods import period_start
from core.domain.read_models import Contribution, LeaderboardRow
from core.domain.value_objects import Period
from core.ports.clock import Clock
from core.ports.repositories import (
    LeaderboardRepository,
    LevelRuleRepository,
    PointRuleRepository,
    SiteConfigRepository,
)


class GetLeaderboard:
    def __init__(
        self,
        leaderboard: LeaderboardRepository,
        point_rules: PointRuleRepository,
        site_config: SiteConfigRepository,
        clock: Clock,
    ) -> None:
        self.leaderboard = leaderboard
        self.point_rules = point_rules
        self.site_config = site_config
        self.clock = clock

    def execute(self, period: Period, page: PageRequest) -> Page[LeaderboardRow]:
        week_start = self.site_config.get().week_start
        since = period_start(
            period, self.clock.now(), week_starts_on_monday=week_start.starts_on_monday
        )
        # Rules are read per request: deactivating a rule takes effect immediately and
        # retroactively (LLD DEC-2 / POL-1 — announce before changing).
        return self.leaderboard.top(since, self.point_rules.active_rules(), page)


class GetContribution:
    def __init__(
        self,
        leaderboard: LeaderboardRepository,
        point_rules: PointRuleRepository,
        level_rules: LevelRuleRepository,
    ) -> None:
        self.leaderboard = leaderboard
        self.point_rules = point_rules
        self.level_rules = level_rules

    def execute(self, user_id: UserId) -> Contribution:
        # Contribution is all-time, so no period window.
        return self.leaderboard.contribution_for(
            user_id,
            self.point_rules.active_rules(),
            self.level_rules.all(),
        )
