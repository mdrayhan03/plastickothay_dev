"""Email notifier via Django's mail layer.

Two-layer design (LLD §6): this adapter speaks the domain's Notifier intent (send_otp,
send_post_approved). The transport - Mailjet in prod via Anymail, console in dev - is Django's
EMAIL_BACKEND, chosen in settings. The domain never sees a subject line or an HTML body.

No Celery, so send() is synchronous inside the request. A short timeout is enforced by the
caller's use case wrapper; a hard failure raises NotificationFailed.
"""

from django.conf import settings
from django.core.mail import send_mail

from core.domain.entities import Post
from core.domain.errors import NotificationFailed
from core.domain.value_objects import OTPPurpose
from core.ports.notifications import Notifier

_OTP_SUBJECTS = {
    OTPPurpose.REGISTRATION: "Verify your PlasticKothay account",
    OTPPurpose.PASSWORD_RESET: "Reset your PlasticKothay password",
}


class MailjetNotifier(Notifier):
    def _from(self) -> str:
        return getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@plastickothay.local")

    def _send(self, to: str, subject: str, body: str) -> None:
        try:
            send_mail(subject, body, self._from(), [to], fail_silently=False)
        except Exception as exc:
            raise NotificationFailed(str(exc)) from exc

    def send_otp(self, to: str, code: int, purpose: OTPPurpose) -> None:
        subject = _OTP_SUBJECTS.get(purpose, "Your PlasticKothay code")
        self._send(to, subject, f"Your verification code is {code}. It expires in 3 minutes.")

    def send_post_approved(self, to: str, post: Post) -> None:
        self._send(
            to,
            "Your PlasticKothay report was approved",
            "Thank you - your report is now visible on the public map.",
        )

    def send_post_rejected(self, to: str, post: Post, reason: str) -> None:
        tail = f"\n\nReason: {reason}" if reason else ""
        self._send(
            to,
            "Your PlasticKothay report was not approved",
            f"Your report was reviewed and could not be published.{tail}",
        )
