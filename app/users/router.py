from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List
from app.users.schemas import UserRead
from app.users.service import UserService
from app.session import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)):
    return UserService.get_all_users(db)

