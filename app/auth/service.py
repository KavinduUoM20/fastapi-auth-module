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
        if not user or not verify_password(password, user.hashed_password):
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

def generate_token_for_user(user: User):
    try:
        return create_access_token({"sub": user.id})
    except Exception as e:
        logger.error(f"Error generating token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate access token")
