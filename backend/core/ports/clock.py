"""Time port.

A port rather than direct ``datetime.now()`` calls so OTP expiry and leaderboard period
boundaries are testable without ``sleep()``.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        """Current instant, tz-aware UTC."""

    @abstractmethod
    def today_local(self) -> date:
        """Today's date in the leaderboard timezone (Asia/Dhaka)."""
