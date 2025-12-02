import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_email(recipient: str, subject: str, body: str, html_body: str = None):
    """
    Send email to a recipient using SMTP
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        body: Plain text email body
        html_body: Optional HTML email body
    """
    if not all([settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, settings.SMTP_FROM_EMAIL]):
        logger.warning("SMTP credentials not fully configured. Skipping email send.")
        return
    
    if not recipient:
        logger.warning("No recipient email address provided. Skipping email send.")
        return
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = recipient
        
        # Add plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            # Enable debug output in development (set to 0 to disable)
            server.set_debuglevel(0)
            
            if settings.SMTP_USE_TLS:
                server.starttls()
            
            # Login with credentials
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            # Send the email
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {recipient}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed for {recipient}: {e}")
        logger.error(f"Please verify your SMTP credentials (username: {settings.SMTP_USERNAME})")
        logger.error("For Zoho Mail: Make sure you're using an App Password, not your regular password.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {recipient}: {e}")
    except Exception as e:
        logger.error(f"Error sending email to {recipient}: {e}", exc_info=True)

