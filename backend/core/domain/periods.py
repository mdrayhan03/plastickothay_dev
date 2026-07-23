"""Leaderboard period boundaries.

Timestamps are stored UTC everywhere, but period boundaries are computed in local time
(LLD §5.4): "this week" for a Dhaka user must not roll over at 06:00 Monday.

The legacy code mixed ``datetime.utcnow()`` and ``datetime.now()``; that is not carried
forward. All input here is tz-aware UTC and all output is tz-aware UTC.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from core.domain.value_objects import Period

LEADERBOARD_TZ = ZoneInfo("Asia/Dhaka")

# Default when no SiteConfig override is supplied. ISO-8601 weeks start Monday.
WEEK_STARTS_ON_MONDAY = True


def period_start(
    period: Period,
    now: datetime,
    tz: ZoneInfo = LEADERBOARD_TZ,
    week_starts_on_monday: bool = WEEK_STARTS_ON_MONDAY,
) -> datetime | None:
    """Inclusive lower bound for a period, as tz-aware UTC. ``None`` means unbounded.

    ``week_starts_on_monday`` is admin-configurable via SiteConfig (LLD app-config): the use
    case reads it and passes it here. The default keeps callers that don't care unchanged.
    """
    if period is Period.ALL:
        return None

    if now.tzinfo is None:
        raise ValueError("`now` must be timezone-aware")

    local = now.astimezone(tz)
    midnight = {"hour": 0, "minute": 0, "second": 0, "microsecond": 0}

    if period is Period.YEAR:
        start = local.replace(month=1, day=1, **midnight)
    elif period is Period.MONTH:
        start = local.replace(day=1, **midnight)
    elif period is Period.WEEK:
        offset = local.weekday() if week_starts_on_monday else (local.weekday() + 1) % 7
        start = (local - timedelta(days=offset)).replace(**midnight)
    else:
        raise ValueError(f"Unhandled period: {period}")

    return start.astimezone(UTC)
