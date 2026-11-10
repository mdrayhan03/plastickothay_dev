"""Badge use cases.

Award-on-read: when a user's badges are fetched, compute their current stats, award any
newly-qualified badges (persisting earned_at), and return the full earned set. This needs no
event system or scheduler - awards are idempotent (unique per user+badge) and the returned set
is always correct even before persistence catches up.
"""

from core.domain.badges import newly_earned
from core.domain.ids import UserId
from core.domain.read_models import EarnedBadge
from core.ports.clock import Clock
from core.ports.repositories import (
    BadgeRepository,
    LeaderboardRepository,
    LevelRuleRepository,
    PointRuleRepository,
)
from core.ports.unit_of_work import UnitOfWork


class GetUserBadges:
    def __init__(
        self,
        badges: BadgeRepository,
        leaderboard: LeaderboardRepository,
        point_rules: PointRuleRepository,
        level_rules: LevelRuleRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.badges = badges
        self.leaderboard = leaderboard
        self.point_rules = point_rules
        self.level_rules = level_rules
        self.uow = uow
        self.clock = clock

    def execute(self, user_id: UserId) -> list[EarnedBadge]:
        contribution = self.leaderboard.contribution_for(
            user_id, self.point_rules.active_rules(), self.level_rules.all()
        )
        earned = self.badges.earned_codes(user_id)
        fresh = newly_earned(contribution, self.badges.active_rules(), earned)

        if fresh:
            now = self.clock.now()
            with self.uow:
                for code in fresh:
                    self.badges.award(user_id, code, now)
                self.uow.commit()

        rules = self.badges.rules_by_code()
        return [
            EarnedBadge(
                code=b.badge_code,
                name=rules[b.badge_code].name if b.badge_code in rules else b.badge_code,
                description=rules[b.badge_code].description if b.badge_code in rules else "",
                icon=rules[b.badge_code].icon if b.badge_code in rules else "",
                earned_at=b.earned_at,
            )
            for b in self.badges.list_earned(user_id)
        ]
