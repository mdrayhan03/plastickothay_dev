"""Public, privacy-limited profile of any user (no email/phone)."""

from core.domain.entities import User
from core.domain.errors import UserNotFound
from core.domain.ids import UserId
from core.domain.read_models import Contribution, EarnedBadge
from core.ports.repositories import (
    BadgeRepository,
    LeaderboardRepository,
    LevelRuleRepository,
    PointRuleRepository,
    UserRepository,
)


class GetPublicProfile:
    """Composes a user's public identity, contribution stats and earned badges. Read-only:
    unlike GetUserBadges it never awards badges, since anyone can view anyone's profile."""

    def __init__(
        self,
        users: UserRepository,
        leaderboard: LeaderboardRepository,
        point_rules: PointRuleRepository,
        level_rules: LevelRuleRepository,
        badges: BadgeRepository,
    ) -> None:
        self.users = users
        self.leaderboard = leaderboard
        self.point_rules = point_rules
        self.level_rules = level_rules
        self.badges = badges

    def execute(self, user_id: UserId) -> tuple[User, Contribution, list[EarnedBadge]]:
        user = self.users.get(user_id)
        if user is None or not user.is_active:
            # 404, not 403: don't confirm a banned/absent account exists.
            raise UserNotFound()

        contribution = self.leaderboard.contribution_for(
            user_id, self.point_rules.active_rules(), self.level_rules.all()
        )

        rules = self.badges.rules_by_code()
        earned = [
            EarnedBadge(
                code=b.badge_code,
                name=rules[b.badge_code].name if b.badge_code in rules else b.badge_code,
                description=rules[b.badge_code].description if b.badge_code in rules else "",
                icon=rules[b.badge_code].icon if b.badge_code in rules else "",
                earned_at=b.earned_at,
            )
            for b in self.badges.list_earned(user_id)
        ]
        return user, contribution, earned
