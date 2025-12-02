from fastapi import APIRouter
from app.users.schemas import UserRead
from app.session import get_db
from fastapi import Depends, HTTPException
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users():
    return {"message": "all good"}

