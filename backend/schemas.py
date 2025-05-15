# File: backend/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Literal, Optional
from datetime import datetime

class UserIn(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    username: str
    email: EmailStr
    createdAt: datetime
    updatedAt: datetime

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionIn(BaseModel):
    model: str
    messages: List[Message]
