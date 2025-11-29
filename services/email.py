"""Email service using SendGrid for PIN delivery."""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from core.config import settings


def send_pin_email(email: str, pin: str, username: str) -> bool:
    """
    Send authentication PIN via email using SendGrid.

    Args:
        email: Recipient email address
        pin: 4-digit PIN
        username: Username for personalization

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # ASCII art email body with retro styling
        email_body = f"""
╔═══════════════════════════════════════╗
║                                       ║
║        🖨️  D I N G  🖨️               ║
║     Retro Receipt Printer Login       ║
║                                       ║
╚═══════════════════════════════════════╝

Hello {username}!

Your login code is:

    ┌─────────────┐
    │             │
    │    {pin}    │
    │             │
    └─────────────┘

This PIN will expire in 10 minutes.

Enter this code on the login screen to access DING.

════════════════════════════════════════

If you didn't request this code, you can safely ignore this email.

Happy dinging! 🎉
"""

        # Create message
        message = Mail(
            from_email=Email(settings.sendgrid_from_email),
            to_emails=To(email),
            subject=f"[DING] Your Login Code: {pin}",
            plain_text_content=Content("text/plain", email_body)
        )

        # Send email
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)

        # Check response
        if response.status_code >= 200 and response.status_code < 300:
            print(f"✅ PIN email sent to {email} (status: {response.status_code})")
            return True
        else:
            print(f"⚠️  Failed to send PIN email to {email} (status: {response.status_code})")
            return False

    except Exception as e:
        print(f"❌ Error sending PIN email: {e}")
        return False
