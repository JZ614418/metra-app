from typing import Optional, UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDBBase(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

class UserUsageStats(BaseModel):
    models_created_this_month: int
    api_calls_this_month: int
    training_minutes_this_month: int
    models_remaining: int
    api_calls_remaining: int
    training_minutes_remaining: int 