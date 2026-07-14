from django.core.mail import send_mail, EmailMessage
from plastickothay.models import Post
from superadmin.models import User, OTP

def test_email() :
    subject = "🌟 Thank You for Making a Difference with Plastickothay"
    body = f"Hi Tester,\n\nThank you for reporting plastic on Plastickothay! Your contribution helps us track and combat plastic pollution more effectively. Every report brings us one step closer to cleaner communities. Stay tuned for updates on how your input is making an impact.\n\nTogether, we can create a plastic-free future.\n\nWarm regards,\nThe Plastickothay Team"

    send_mail(
            subject,
            body,
            'contact.plastickothay@gmail.com',
            ['phylosopherhossain2022@gmail.com'],
            fail_silently=False,
        )

def test_html_email():
    html_content = """
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Hello from Django!</h2>
                <p style="font-size: 16px; color: #555555;">
                    This is a test HTML email sent from your Django project.
                </p>
                <p style="font-size: 14px; color: #888888;">
                    <em>Sent on: {{ current_date }}</em>
                </p>
                <hr />
                <p style="font-size: 12px; color: #aaaaaa;">© 2025 Your Company Name</p>
            </div>
        </body>
    </html>
    """

    email = EmailMessage(
        subject='📬 Django HTML Email Test',
        body=html_content,
        from_email='contact.plastickothay@gmail.com',
        to=['phylosopherhossain2022@gmail.com'],
    )
    email.content_subtype = 'html'  # Specify that the body is HTML

    # Optional: attach a file
    # email.attach_file('/path/to/file.pdf')

    email.send()

def post_mail(post: Post) :
    subject = "🌟 Thank You for Making a Difference with Plastickothay"
    body = f"Hi {post.name},\n\nThank you for reporting plastic on Plastickothay! Your contribution helps us track and combat plastic pollution more effectively. Every report brings us one step closer to cleaner communities. Stay tuned for updates on how your input is making an impact.\n\nTogether, we can create a plastic-free future.\n\nWarm regards,\nThe Plastickothay Team"
    
    try :
        send_mail(
            subject,
            body,
            'contact.plastickothay@gmail.com',
            [post.email],
            fail_silently=False,
        )
        return True
    except :
        return False
    
def account_verification_mail(user: User, otp: OTP):
    subject = "🔐 Verify Your Plastickothay Account"
    body = (
        f"Hi {user.first_name} {user.last_name},\n\n"
        f"Welcome to Plastickothay! To activate your account, please verify your email address.\n\n"
        f"Your verification code is:\n\n"
        f"    {otp.code}\n\n"
        f"This code will expire in 3 minutes, so please use it promptly.\n\n"
        f"If you did not create this account, please ignore this email.\n\n"
        f"Thank you for joining us in the fight against plastic pollution!\n\n"
        f"— The Plastickothay Team"
    )

    try:
        send_mail(
            subject,
            body,
            'contact.plastickothay@gmail.com',
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # optional: log error e
        return False
    
def password_reset_mail(user: User, otp: OTP):
    subject = "🔐 Reset Your Plastickothay Password"
    body = (
        f"Hi {user.first_name} {user.last_name},\n\n"
        f"We received a request to reset the password for your Plastickothay account.\n\n"
        f"Your password reset code is:\n\n"
        f"    {otp.code}\n\n"
        f"This code will expire in 3 minutes, so please use it promptly.\n\n"
        f"If you did not request a password reset, please ignore this email.\n\n"
        f"Thank you for helping us fight plastic pollution!\n\n"
        f"— The Plastickothay Team"
    )

    try:
        send_mail(
            subject,
            body,
            'contact.plastickothay@gmail.com',
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # optional: log error e
        return False