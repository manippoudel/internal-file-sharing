"""Authentication schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response schema"""
    success: bool
    token: str
    user_id: uuid.UUID
    username: str
    role: str
    must_change_password: bool
    message: str


class LogoutRequest(BaseModel):
    """Logout request schema"""
    token: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=12)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password complexity"""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class TokenValidationResponse(BaseModel):
    """Token validation response"""
    valid: bool
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    role: Optional[str] = None
