"""Shared fixtures.

Note what is missing: any Django setup, any database, any settings module. If this file ever
needs one, the hexagon has sprung a leak.
"""

from datetime import UTC, datetime

import pytest

from core.domain.entities import Post, User
from core.domain.ids import UserId
from core.domain.value_objects import (
    GeoPoint,
    ImageRef,
    PostStatus,
    Reporter,
    Role,
    Severity,
)
from tests.fakes.repositories import (
    InMemoryContactRepository,
    InMemoryEngagementRepository,
    InMemoryFeedbackRepository,
    InMemoryLeaderboardRepository,
    InMemoryLevelRuleRepository,
    InMemoryModerationLogRepository,
    InMemoryOTPRepository,
    InMemoryPointRuleRepository,
    InMemoryPostRepository,
    InMemorySiteConfigRepository,
    InMemoryUserRepository,
)
from tests.fakes.system import (
    FakeClock,
    FakeImageStorage,
    FakeNotifier,
    FakePasswordHasher,
    FakeTokenService,
    FakeUnitOfWork,
)

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def otps() -> InMemoryOTPRepository:
    return InMemoryOTPRepository()


@pytest.fixture
def posts() -> InMemoryPostRepository:
    return InMemoryPostRepository()


@pytest.fixture
def engagements() -> InMemoryEngagementRepository:
    return InMemoryEngagementRepository()


@pytest.fixture
def point_rules() -> InMemoryPointRuleRepository:
    return InMemoryPointRuleRepository()


@pytest.fixture
def level_rules() -> InMemoryLevelRuleRepository:
    return InMemoryLevelRuleRepository()


@pytest.fixture
def leaderboard(posts, engagements, users, clock) -> InMemoryLeaderboardRepository:
    return InMemoryLeaderboardRepository(posts, engagements, users, clock)


@pytest.fixture
def site_config() -> InMemorySiteConfigRepository:
    return InMemorySiteConfigRepository()


@pytest.fixture
def feedback() -> InMemoryFeedbackRepository:
    return InMemoryFeedbackRepository()


@pytest.fixture
def contact() -> InMemoryContactRepository:
    return InMemoryContactRepository()


@pytest.fixture
def moderation_log() -> InMemoryModerationLogRepository:
    return InMemoryModerationLogRepository()


@pytest.fixture
def images() -> FakeImageStorage:
    return FakeImageStorage()


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def tokens(clock) -> FakeTokenService:
    return FakeTokenService(clock)


# --- builders --------------------------------------------------------------


@pytest.fixture
def make_user(users, clock):
    def _make(
        username: str = "alice",
        *,
        role: Role = Role.USER,
        is_verified: bool = True,
        is_active: bool = True,
        password: str = "secret",
    ) -> User:
        return users.add(
            User(
                id=None,
                username=username,
                email=f"{username}@example.com",
                first_name=username.capitalize(),
                last_name="Tester",
                phone="+8801700000000",
                role=role,
                is_verified=is_verified,
                is_active=is_active,
                date_joined=clock.now(),
            ),
            password=password,
        )

    return _make


@pytest.fixture
def make_post(posts, clock):
    def _make(
        *,
        reporter_id: UserId | None = None,
        status: PostStatus = PostStatus.APPROVED,
        severity: Severity = Severity.MODERATE,
        approved_at: datetime | None = None,
        created: datetime | None = None,
    ) -> Post:
        is_approved = status is PostStatus.APPROVED
        return posts.add(
            Post(
                id=None,
                reporter=Reporter("Anon Reporter", "anon@example.com", "+8801711111111"),
                reporter_id=reporter_id,
                severity=severity,
                image=ImageRef(provider="fake", external_id="img-1"),
                location=GeoPoint(23.8103, 90.4125),  # Dhaka
                description="Plastic pile near the canal.",
                status=status,
                created=created or clock.now(),
                approved_at=approved_at or (clock.now() if is_approved else None),
            )
        )

    return _make
