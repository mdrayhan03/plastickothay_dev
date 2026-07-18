"""Composition root — the one place ports are wired to concrete adapters.

Plain factory functions, no DI framework: a monolith this size does not need one. The API
layer (B2+) calls these to build use cases per request. LeaderboardRepository arrives in B5.
"""

from adapters.persistence.django_orm.repositories import (
    DjangoContactRepository,
    DjangoEngagementRepository,
    DjangoFeedbackRepository,
    DjangoLevelRuleRepository,
    DjangoModerationLogRepository,
    DjangoOTPRepository,
    DjangoPointRuleRepository,
    DjangoPostRepository,
    DjangoUserRepository,
)
from adapters.persistence.django_orm.unit_of_work import DjangoUnitOfWork
from adapters.security.password_hasher import DjangoPasswordHasher
from adapters.system.clock import SystemClock


def clock():
    return SystemClock()


def unit_of_work():
    return DjangoUnitOfWork()


def password_hasher():
    return DjangoPasswordHasher()


def users():
    return DjangoUserRepository()


def otps():
    return DjangoOTPRepository()


def posts():
    return DjangoPostRepository()


def engagements():
    return DjangoEngagementRepository()


def point_rules():
    return DjangoPointRuleRepository()


def level_rules():
    return DjangoLevelRuleRepository()


def feedback():
    return DjangoFeedbackRepository()


def contact():
    return DjangoContactRepository()


def moderation_log():
    return DjangoModerationLogRepository()
