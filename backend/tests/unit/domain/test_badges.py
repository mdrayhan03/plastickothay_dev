"""Badge award rules - pure, no DB."""

from core.domain.badges import newly_earned, qualifies
from core.domain.entities import BadgeRule
from core.domain.ids import UserId
from core.domain.read_models import Contribution
from core.domain.value_objects import BadgeCriteria


def contribution(**over) -> Contribution:
    defaults = dict(
        user_id=UserId(1),
        total_points=0,
        posts_approved=0,
        likes_received=0,
        likes_given=0,
        level=1,
        level_title="Newcomer",
        points_to_next_level=100,
        progress_percentage=0.0,
    )
    defaults.update(over)
    return Contribution(**defaults)


RULES = [
    BadgeRule("first", "First", "", BadgeCriteria.POSTS_APPROVED, 1, True),
    BadgeRule("ten", "Ten", "", BadgeCriteria.POSTS_APPROVED, 10, True),
    BadgeRule("liked", "Liked", "", BadgeCriteria.LIKES_RECEIVED, 25, True),
    BadgeRule("champ", "Champ", "", BadgeCriteria.POINTS_TOTAL, 1500, True),
    BadgeRule("off", "Off", "", BadgeCriteria.POSTS_APPROVED, 1, False),  # inactive
]


class TestQualifies:
    def test_meets_threshold(self):
        assert qualifies(RULES[0], contribution(posts_approved=1)) is True

    def test_below_threshold(self):
        assert qualifies(RULES[1], contribution(posts_approved=9)) is False

    def test_inactive_never_qualifies(self):
        assert qualifies(RULES[4], contribution(posts_approved=100)) is False


class TestNewlyEarned:
    def test_awards_qualifying_not_yet_earned(self):
        c = contribution(posts_approved=10, likes_received=25, total_points=1500)
        fresh = newly_earned(c, RULES, already_earned=set())
        assert set(fresh) == {"first", "ten", "liked", "champ"}

    def test_skips_already_earned(self):
        c = contribution(posts_approved=10)
        fresh = newly_earned(c, RULES, already_earned={"first"})
        assert "first" not in fresh
        assert "ten" in fresh

    def test_nothing_when_below_all_thresholds(self):
        assert newly_earned(contribution(), RULES, set()) == []

    def test_inactive_rule_never_awarded(self):
        fresh = newly_earned(contribution(posts_approved=100), RULES, set())
        assert "off" not in fresh
