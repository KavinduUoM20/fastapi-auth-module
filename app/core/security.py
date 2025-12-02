import logging
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

# Use bcrypt directly - this is the most reliable approach
BCRYPT_ROUNDS = 12

# Maximum password length in bytes (bcrypt limitation)
MAX_PASSWORD_BYTES = 72


def _validate_and_prepare_password(password: str) -> bytes:
    """
    Validate password and convert to bytes, ensuring it's within bcrypt's 72-byte limit.
    Raises ValueError if password is invalid or too long.
    """
    if not isinstance(password, str):
        raise ValueError(f"Password must be a string, got {type(password).__name__}")
    
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Encode to UTF-8 bytes
    password_bytes = password.encode('utf-8')
    byte_length = len(password_bytes)
    
    # Strict validation - reject passwords that exceed 72 bytes
    if byte_length > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password is too long: {len(password)} characters = {byte_length} bytes. "
            f"Maximum allowed is {MAX_PASSWORD_BYTES} bytes. "
            f"Please use a shorter password."
        )
    
    return password_bytes


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password string
        
    Returns:
        Hashed password as string
        
    Raises:
        ValueError: If password is invalid or too long
    """
    try:
        # Validate and prepare password (ensures it's <= 72 bytes)
        password_bytes = _validate_and_prepare_password(password)
        
        # Generate salt
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        
        # Hash the password
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        
        # Convert bytes to string for storage
        hashed = hashed_bytes.decode('utf-8')
        
        if not hashed or len(hashed) == 0:
            raise ValueError("Password hashing returned empty result")
        
        return hashed
        
    except ValueError:
        # Re-raise ValueError as-is (these are validation errors)
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Unexpected error hashing password: {error_msg}", exc_info=True)
        
        # Provide user-friendly error message
        if "cannot be longer than 72 bytes" in error_msg.lower():
            byte_length = len(password.encode('utf-8'))
            raise ValueError(
                f"Password is too long ({byte_length} bytes). "
                f"Maximum allowed is {MAX_PASSWORD_BYTES} bytes."
            )
        
        raise ValueError(f"Failed to hash password: {error_msg}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        if not plain_password or not hashed_password:
            return False
        
        # Prepare password bytes (truncate if needed to match hashing behavior)
        try:
            password_bytes = _validate_and_prepare_password(plain_password)
        except ValueError:
            # If password is too long, truncate it to match how it was hashed
            password_bytes = plain_password.encode('utf-8')[:MAX_PASSWORD_BYTES]
        
        # Convert hashed_password to bytes if it's a string
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
        
        # Verify using bcrypt
        return bcrypt.checkpw(password_bytes, hashed_bytes)
        
    except Exception as e:
        logger.error(f"Error verifying password: {e}", exc_info=True)
        return False

def create_access_token(data: dict, expires_minutes: int = None):
    try:
        to_encode = data.copy()
        # Use uppercase attribute name to match Settings class
        # Default to 7 days (10080 minutes) if not provided
        default_expire_minutes = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 60 * 24 * 7)
        expire_minutes = expires_minutes or default_expire_minutes
        
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
        to_encode["exp"] = expire
        
        # Use uppercase attribute names to match Settings class
        jwt_secret = getattr(settings, 'JWT_SECRET', '')
        jwt_algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
        
        if not jwt_secret:
            raise ValueError("JWT_SECRET is not configured")
        
        return jwt.encode(to_encode, jwt_secret, jwt_algorithm)
    except JWTError as e:
        logger.error(f"JWT encoding error: {e}", exc_info=True)
        raise ValueError("Failed to create access token")
    except AttributeError as e:
        logger.error(f"Configuration error: {e}", exc_info=True)
        raise ValueError(f"Configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating access token: {e}", exc_info=True)
        raise ValueError(f"Failed to create access token: {str(e)}")