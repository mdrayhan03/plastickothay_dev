"""Email template definitions with consistent HTML layout (Header & Footer)."""

from typing import Tuple
from core.domain.entities import Post
from core.domain.value_objects import OTPPurpose

# Global Header & Footer templates
_HEADER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; color: #333333; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .header { background-color: #059669; padding: 24px; text-align: center; }
        .header h1 { color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 0.5px; }
        .content { padding: 32px 24px; line-height: 1.6; }
        .footer { background-color: #f8fafc; padding: 16px 24px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }
        .otp-box { font-size: 32px; font-weight: bold; color: #059669; letter-spacing: 6px; padding: 16px; background: #ecfdf5; display: inline-block; border-radius: 6px; margin: 16px 0; }
        .btn { display: inline-block; padding: 12px 24px; background-color: #059669; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PlasticKothay</h1>
        </div>
        <div class="content">
"""

_FOOTER_HTML = """
        </div>
        <div class="footer">
            <p>© PlasticKothay. All rights reserved.</p>
            <p>You are receiving this email because of activity associated with your account.</p>
        </div>
    </div>
</body>
</html>
"""


def _wrap_html(content: str) -> str:
    """Wraps body content in the standard header and footer."""
    return f"{_HEADER_HTML}{content}{_FOOTER_HTML}"


class EmailTemplateRenderer:
    """Generates subject and HTML content for domain notifications."""

    @staticmethod
    def render_otp(code: int, purpose: OTPPurpose) -> Tuple[str, str, str]:
        subjects = {
            OTPPurpose.REGISTRATION: "Verify your PlasticKothay account",
            OTPPurpose.PASSWORD_RESET: "Reset your PlasticKothay password",
        }
        subject = subjects.get(purpose, "Your PlasticKothay code")

        html_content = f"""
            <h2>Verification Code</h2>
            <p>Use the verification code below to complete your request:</p>
            <div style="text-align: center;">
                <div class="otp-box">{code}</div>
            </div>
            <p>This code will expire in <strong>3 minutes</strong>. If you did not request this code, please ignore this email.</p>
        """
        plain_text = f"Your verification code is {code}. It expires in 3 minutes."

        return subject, _wrap_html(html_content), plain_text

    @staticmethod
    def render_post_approved(post: Post) -> Tuple[str, str, str]:
        subject = "Your PlasticKothay report was approved"
        html_content = """
            <h2>Report Approved! 🎉</h2>
            <p>Thank you for contributing. Your report has been reviewed and is now live on the public map.</p>
            <p>Together, we are making our community cleaner!</p>
        """
        plain_text = "Thank you - your report is now visible on the public map."

        return subject, _wrap_html(html_content), plain_text

    @staticmethod
    def render_post_rejected(post: Post, reason: str) -> Tuple[str, str, str]:
        subject = "Your PlasticKothay report was not approved"
        reason_block = f"<p><strong>Reason provided:</strong> {reason}</p>" if reason else ""
        tail = f"\n\nReason: {reason}" if reason else ""

        html_content = f"""
            <h2>Report Status Update</h2>
            <p>Your report was reviewed, but unfortunately it could not be published at this time.</p>
            {reason_block}
            <p>If you believe this was an error, feel free to submit an updated report.</p>
        """
        plain_text = f"Your report was reviewed and could not be published.{tail}"

        return subject, _wrap_html(html_content), plain_text