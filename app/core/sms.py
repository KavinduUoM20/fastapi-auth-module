import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

SMS_API_URL = "https://app.text.lk/api/v3/sms/send"

def send_sms(recipient: str, message: str):
    """
    Send SMS to a recipient using the Text.lk API
    
    Args:
        recipient: Phone number in format like "94710000000"
        message: SMS message content
    """
    if not settings.SMS_BEARER_TOKEN or not settings.SMS_SENDER_ID:
        logger.warning("SMS credentials not configured. Skipping SMS send.")
        return
    
    if not recipient:
        logger.warning("No recipient phone number provided. Skipping SMS send.")
        return
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.SMS_BEARER_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "recipient": recipient,
            "sender_id": settings.SMS_SENDER_ID,
            "type": "plain",
            "message": message
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.post(SMS_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"SMS sent successfully to {recipient}")
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error sending SMS to {recipient}: {e}")
    except Exception as e:
        logger.error(f"Error sending SMS to {recipient}: {e}", exc_info=True)

