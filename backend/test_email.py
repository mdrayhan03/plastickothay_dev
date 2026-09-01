import os
import django

# Set settings module to prod so it loads anymail/mailjet
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
os.environ["EMAIL_BACKEND"] = "anymail.backends.mailjet.EmailBackend"
os.environ["DEFAULT_FROM_EMAIL"] = "contact.plastickothay@gmail.com"
os.environ["MAILJET_API_KEY"] = "9bd8e0dc67433c3b92ed0cbe6fe4830b"
os.environ["MAILJET_SECRET_KEY"] = "f39f4819f7ee15c87c45894805f5334e"

django.setup()

from django.core.mail import EmailMultiAlternatives
from core.domain.templates import EmailTemplateRenderer
from core.domain.value_objects import OTPPurpose

SENDER = "contact.plastickothay@gmail.com"
RECIPIENTS = ["contact.plastickothay@gmail.com", "mostafaizurrahman2021@gmail.com"]

try:
    print("Generating HTML email using EmailTemplateRenderer...")
    
    # 1. Render subject, styled HTML, and plain text using the renderer
    test_code = 482910
    subject, html_body, plain_text = EmailTemplateRenderer.render_otp(
        code=test_code,
        purpose=OTPPurpose.REGISTRATION
    )

    # 2. Construct the Django multi-part message
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=SENDER,
        to=RECIPIENTS,
    )
    
    # Attach HTML alternative so clients render full styling (header/footer/buttons)
    msg.attach_alternative(html_body, "text/html")

    print(f"Sending test email via Mailjet to {RECIPIENTS}...")
    sent_count = msg.send(fail_silently=False)

    if sent_count > 0:
        print("✅ HTML Email sent successfully! Check your inbox.")
    else:
        print("⚠️ Send completed, but 0 messages were dispatched.")

except Exception as e:
    print(f"❌ Failed to send email: {e}")