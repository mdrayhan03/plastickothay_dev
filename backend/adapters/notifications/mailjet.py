"""Email notifier via Django's mail layer.

Two-layer design (LLD §6): this adapter speaks the domain's Notifier intent (send_otp,
send_post_approved). The transport - Mailjet in prod via Anymail, console in dev - is Django's
EMAIL_BACKEND, chosen in settings. The domain never sees a subject line or an HTML body.

No Celery, so send() is synchronous inside the request. A short timeout is enforced by the
caller's use case wrapper; a hard failure raises NotificationFailed.
"""

"""Email notifier via Django's mail layer."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from core.domain.entities import Post
from core.domain.errors import NotificationFailed
from core.domain.value_objects import OTPPurpose
from core.ports.notifications import Notifier
from core.domain.templates import EmailTemplateRenderer


class MailjetNotifier(Notifier):
    def _from(self) -> str:
        return getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@plastickothay.local")

    def _send(self, to: str, subject: str, html_body: str, plain_text: str) -> None:
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_text,
                from_email=self._from(),
                to=[to],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
        except Exception as exc:
            raise NotificationFailed(str(exc)) from exc

    def send_otp(self, to: str, code: int, purpose: OTPPurpose) -> None:
        subject, html_body, plain_text = EmailTemplateRenderer.render_otp(code, purpose)
        self._send(to, subject, html_body, plain_text)

    def send_post_approved(self, to: str, post: Post) -> None:
        subject, html_body, plain_text = EmailTemplateRenderer.render_post_approved(post)
        self._send(to, subject, html_body, plain_text)

    def send_post_rejected(self, to: str, post: Post, reason: str) -> None:
        subject, html_body, plain_text = EmailTemplateRenderer.render_post_rejected(post, reason)
        self._send(to, subject, html_body, plain_text)
