import logging
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError

from app.users.models import User
from app.users.schemas import UserCreate, UserRead
from app.core.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)

def register_user(user_data, db: Session):
    try:
        # Check if user already exists
        existing = db.exec(select(User).where(User.email == user_data.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            mobile_phone=user_data.mobile_phone,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in register_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in register_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while registering user")

def authenticate_user(email: str, password: str, db: Session):
    try:
        user = db.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is OAuth user (no password)
        if user.hashed_password is None:
            raise HTTPException(status_code=401, detail="This account was created with OAuth. Please sign in with Google.")
        
        # Verify password for email/password users
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return user
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in authenticate_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in authenticate_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while authenticating user")

def create_or_get_oauth_user(user_info: dict, provider: str, provider_id: str, db: Session):
    """
    Create a new OAuth user or return existing user.
    
    Args:
        user_info: User information from OAuth provider
        provider: OAuth provider name (e.g., 'google')
        provider_id: Unique ID from OAuth provider
        db: Database session
    
    Returns:
        Tuple of (User object, is_new_user: bool)
    """
    try:
        email = user_info.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by OAuth provider")
        
        # Check if user exists by email
        existing_user = db.exec(select(User).where(User.email == email)).first()
        
        if existing_user:
            # Update provider info if not set
            if existing_user.provider is None:
                existing_user.provider = provider
                existing_user.provider_id = provider_id
                db.add(existing_user)
                db.commit()
                db.refresh(existing_user)
            return existing_user, False  # Existing user, not new
        
        # Create new OAuth user
        # Extract name from user_info
        first_name = user_info.get('given_name') or user_info.get('first_name') or None
        last_name = user_info.get('family_name') or user_info.get('last_name') or None
        # If name is in 'name' field, try to split it
        if not first_name and user_info.get('name'):
            name_parts = user_info.get('name', '').split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
        
        new_user = User(
            email=email,
            hashed_password=None,  # OAuth users don't have passwords
            first_name=first_name,
            last_name=last_name,
            provider=provider,
            provider_id=provider_id,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user, True  # New user created
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in create_or_get_oauth_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in create_or_get_oauth_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while creating OAuth user")

def generate_token_for_user(user: User):
    try:
        return create_access_token({"sub": user.id})
    except Exception as e:
        logger.error(f"Error generating token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate access token")
