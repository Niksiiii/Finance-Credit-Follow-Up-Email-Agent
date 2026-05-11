"""
Email sender with dry-run mode support.
Supports SMTP for real sending, and logs for dry-run simulation.
"""

import smtplib
import loggings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SendResult:
    """Result of an email send attempt."""
    status: str  # DRY_RUN | SENT | FAILED
    error_message: str = ""


def send_email(
    to_email: str,
    subject: str,
    body: str,
    dry_run: bool = True,
) -> SendResult:
    """
    Send an email via SMTP or simulate in dry-run mode.
    
    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        body: Email body text.
        dry_run: If True, log the email instead of sending.
    
    Returns:
        SendResult with status and any error message.
    """
    if dry_run:
        logger.info(
            f"[DRY-RUN] Email to: {to_email}\n"
            f"  Subject: {subject}\n"
            f"  Body preview: {body[:200]}..."
        )
        return SendResult(status="DRY_RUN")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
        msg["To"] = to_email

        # Plain text body
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # HTML version (wrap plain text in basic HTML)
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            {''.join(f'<p>{line}</p>' if line.strip() else '<br>' for line in body.split(chr(10)))}
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SENDER_EMAIL, to_email, msg.as_string())

        logger.info(f"[SENT] Email to: {to_email} | Subject: {subject}")
        return SendResult(status="SENT")

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"[FAILED] SMTP auth error for {to_email}: {e}")
        return SendResult(status="FAILED", error_message=f"SMTP authentication failed: {e}")
    except smtplib.SMTPException as e:
        logger.error(f"[FAILED] SMTP error for {to_email}: {e}")
        return SendResult(status="FAILED", error_message=f"SMTP error: {e}")
    except Exception as e:
        logger.error(f"[FAILED] Unexpected error sending to {to_email}: {e}")
        return SendResult(status="FAILED", error_message=str(e))
