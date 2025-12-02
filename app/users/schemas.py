from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="john@example.com")
    password: str = Field(..., repr=False, min_length=1, max_length=72)
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    mobile_phone: Optional[str] = Field(None, example="+1234567890")
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 1:
            raise ValueError("Password cannot be empty")
        
        # Check byte length (bcrypt limit is 72 bytes, not characters)
        # Unicode characters can be multiple bytes
        byte_length = len(v.encode('utf-8'))
        if byte_length > 72:
            raise ValueError(
                f"Password cannot exceed 72 bytes (bcrypt limitation). "
                f"Your password is {len(v)} characters ({byte_length} bytes). "
                f"Please use a shorter password or avoid multi-byte characters."
            )
        
        # Also check character length as a reasonable limit
        if len(v) > 72:
            raise ValueError("Password cannot exceed 72 characters")
        
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="john@example.com")
    password: str = Field(..., repr=False, min_length=1)


class UserRead(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_phone: Optional[str] = None
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class UserOut(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_phone: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"