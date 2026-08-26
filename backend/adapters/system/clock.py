"""System clock adapter."""

from datetime import UTC, date, datetime

from core.domain.periods import LEADERBOARD_TZ
from core.ports.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)

    def today_local(self) -> date:
        return datetime.now(LEADERBOARD_TZ).date()
