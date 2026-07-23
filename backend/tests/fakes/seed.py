"""Default rule seed data.

Point values are the agreed scheme (LLD §5.2). Comment rules are seeded INACTIVE — the
model supports comments so shipping them later is a flag flip, not a migration.
"""

from core.domain.entities import BadgeRule, LevelRule
from core.domain.points import (
    RULE_COMMENT_GIVEN,
    RULE_COMMENT_RECEIVED,
    RULE_LIKE_GIVEN,
    RULE_LIKE_RECEIVED,
    RULE_POST_APPROVED,
)
from core.domain.value_objects import BadgeCriteria

DEFAULT_POINT_RULES = {
    RULE_POST_APPROVED: 100,
    RULE_LIKE_RECEIVED: 3,
    RULE_LIKE_GIVEN: 1,
    RULE_COMMENT_RECEIVED: 0,  # inactive
    RULE_COMMENT_GIVEN: 0,  # inactive
}

# PLACEHOLDER — needs a product decision. The legacy code used "every 5 points = 1 level",
# which is meaningless now that one approved post is worth 100. These thresholds are a
# guess; they are table-driven precisely so they can be changed without code.
DEFAULT_LEVEL_RULES = [
    LevelRule(level=1, min_points=0, title="Newcomer"),
    LevelRule(level=2, min_points=100, title="Reporter"),
    LevelRule(level=3, min_points=300, title="Contributor"),
    LevelRule(level=4, min_points=700, title="Guardian"),
    LevelRule(level=5, min_points=1500, title="Champion"),
]

DEFAULT_BADGE_RULES = [
    BadgeRule("first_report", "First Report", "First approved report.",
              BadgeCriteria.POSTS_APPROVED, 1, True, "🌱"),
    BadgeRule("reporter_10", "Active Reporter", "10 approved reports.",
              BadgeCriteria.POSTS_APPROVED, 10, True, "📸"),
    BadgeRule("well_liked", "Well Liked", "25 likes received.",
              BadgeCriteria.LIKES_RECEIVED, 25, True, "❤️"),
    BadgeRule("champion", "Champion", "1500 points.",
              BadgeCriteria.POINTS_TOTAL, 1500, True, "👑"),
]
