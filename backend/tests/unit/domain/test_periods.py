"""Period boundaries must be computed in Dhaka time, not UTC.

The legacy code mixed datetime.utcnow() and datetime.now(). If periods bucketed in UTC, the
weekly leaderboard would reset at 06:00 Monday local — mid-morning for every user.
"""

from datetime import UTC, datetime

import pytest

from core.domain.periods import LEADERBOARD_TZ, period_start
from core.domain.value_objects import Period


class TestPeriodStart:
    def test_all_is_unbounded(self):
        assert period_start(Period.ALL, datetime(2026, 7, 17, tzinfo=UTC)) is None

    def test_requires_aware_datetime(self):
        with pytest.raises(ValueError):
            period_start(Period.WEEK, datetime(2026, 7, 17))

    def test_week_starts_monday_local_midnight(self):
        # Friday 17 Jul 2026, 12:00 UTC == 18:00 Dhaka. Week began Mon 13 Jul 00:00 Dhaka.
        start = period_start(Period.WEEK, datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
        local = start.astimezone(LEADERBOARD_TZ)
        assert (local.year, local.month, local.day) == (2026, 7, 13)
        assert (local.hour, local.minute) == (0, 0)
        assert local.weekday() == 0

    def test_month_starts_first_local_midnight(self):
        start = period_start(Period.MONTH, datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
        local = start.astimezone(LEADERBOARD_TZ)
        assert (local.day, local.hour) == (1, 0)
        assert local.month == 7

    def test_year_starts_jan_first_local_midnight(self):
        start = period_start(Period.YEAR, datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
        local = start.astimezone(LEADERBOARD_TZ)
        assert (local.month, local.day, local.hour) == (1, 1, 0)

    def test_boundary_is_dhaka_midnight_not_utc_midnight(self):
        """The whole reason this module exists.

        18:30 UTC Sunday is already 00:30 Monday in Dhaka, so the new week has begun even
        though it is still Sunday in UTC.
        """
        sunday_evening_utc = datetime(2026, 7, 12, 18, 30, tzinfo=UTC)
        start = period_start(Period.WEEK, sunday_evening_utc)
        local = start.astimezone(LEADERBOARD_TZ)
        assert (local.month, local.day) == (7, 13)  # Monday, not the previous week

    def test_returns_utc(self):
        start = period_start(Period.WEEK, datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
        assert start.tzinfo is not None
        assert start.utcoffset().total_seconds() == 0
