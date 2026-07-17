"""Leaderboard and per-user contribution.

Both delegate the calculation to LeaderboardRepository — the strategy port. Production uses
raw Postgres SQL; the fake uses core.domain.points. The use case only decides the period
window and supplies the active rules, so swapping the calculation never touches this file.
"""

from core.domain.ids import UserId
from core.domain.pagination import Page, PageRequest
from core.domain.read_models import Contribution, LeaderboardRow
from core.domain.value_objects import Period
from core.ports.repositories import (
    LeaderboardRepository,
    LevelRuleRepository,
    PointRuleRepository,
)


class GetLeaderboard:
    def __init__(
        self,
        leaderboard: LeaderboardRepository,
        point_rules: PointRuleRepository,
    ) -> None:
        self.leaderboard = leaderboard
        self.point_rules = point_rules

    def execute(self, period: Period, page: PageRequest) -> Page[LeaderboardRow]:
        # Rules are read per request: deactivating a rule takes effect immediately and
        # retroactively (LLD DEC-2 / POL-1 — announce before changing).
        return self.leaderboard.top(period, self.point_rules.active_rules(), page)


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
        return self.leaderboard.contribution_for(
            user_id,
            self.point_rules.active_rules(),
            self.level_rules.all(),
        )
