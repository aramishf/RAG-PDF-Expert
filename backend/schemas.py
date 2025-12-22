from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    initials: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    initials: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Document schemas
class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    
    class Config:
        from_attributes = True

# Chat message schemas
class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
