"""Badge award rules - pure domain logic.

A badge is earned when a user's stat reaches the rule's threshold. Awards are permanent: once
earned they stay, even if the stat later drops (achievements don't un-earn). So the only thing
computed here is which *not-yet-earned* badges a user now qualifies for.
"""

from collections.abc import Iterable

from core.domain.entities import BadgeRule
from core.domain.read_models import Contribution
from core.domain.value_objects import BadgeCriteria


def _stat_for(contribution: Contribution, criteria: BadgeCriteria) -> int:
    return {
        BadgeCriteria.POSTS_APPROVED: contribution.posts_approved,
        BadgeCriteria.LIKES_RECEIVED: contribution.likes_received,
        BadgeCriteria.LIKES_GIVEN: contribution.likes_given,
        BadgeCriteria.POINTS_TOTAL: contribution.total_points,
    }[criteria]


def qualifies(rule: BadgeRule, contribution: Contribution) -> bool:
    return rule.active and _stat_for(contribution, rule.criteria) >= rule.threshold


def newly_earned(
    contribution: Contribution,
    rules: Iterable[BadgeRule],
    already_earned: set[str],
) -> list[str]:
    """Codes of active badges the user now qualifies for but has not been awarded yet."""
    return [
        rule.code
        for rule in rules
        if rule.code not in already_earned and qualifies(rule, contribution)
    ]
