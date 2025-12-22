from sqlmodel import Session, select
from fastapi import HTTPException, status
from .models import User
from .schemas import UserCreate, UserRead
from app.core.security import hash_password 

class UserService:

    @staticmethod
    def create_user(session: Session, data: UserCreate) -> UserRead:
        # Check if user already exists
        existing = session.exec(select(User).where(User.email == data.email)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password and create user
        hashed = hash_password(data.password)
        user = User(
            email=data.email,
            hashed_password=hashed,
            first_name=data.first_name,
            last_name=data.last_name,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        # Return as Pydantic model
        return UserRead.model_validate(user)

    @staticmethod
    def get_user_by_email(session: Session, email: str) -> User | None:
        return session.exec(select(User).where(User.email == email)).first()

    @staticmethod
    def get_all_users(session: Session) -> list[UserRead]:
        users = session.exec(select(User)).all()
        return [UserRead.model_validate(user) for user in users]