"""Notification port.

Speaks domain intent ("send an OTP"), not transport ("send this HTML with this subject").
The transport strategy is Django's EMAIL_BACKEND, which lives *inside* the Mailjet adapter
— two layers, deliberately: this port is what lets tests fake email entirely, and it stops
subjects and templates leaking into use cases.
"""

from abc import ABC, abstractmethod

from core.domain.entities import Post
from core.domain.value_objects import OTPPurpose


class Notifier(ABC):
    @abstractmethod
    def send_otp(self, to: str, code: int, purpose: OTPPurpose) -> None:
        """Raises NotificationFailed."""

    @abstractmethod
    def send_post_approved(self, to: str, post: Post) -> None: ...

    @abstractmethod
    def send_post_rejected(self, to: str, post: Post, reason: str) -> None: ...
