import logging
import os
from pydantic_settings import BaseSettings
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    SMS_BEARER_TOKEN: str = ""
    SMS_SENDER_ID: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

try:
    settings = Settings()
except ValidationError as e:
    logger.error(f"Configuration validation error: {e}")
    # Provide defaults or raise with helpful message
    missing_vars = [err["loc"][0] for err in e.errors() if err["type"] == "missing"]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please ensure a .env file exists with all required variables")
    raise
except Exception as e:
    logger.error(f"Error loading settings: {e}", exc_info=True)
    raise