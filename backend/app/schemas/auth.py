"""Authentication schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """User registration request.

    Security: Includes honeypot field for bot detection.
    The 'website' field should always be empty - bots often fill hidden fields.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    # Honeypot field - should be empty (hidden from real users)
    website: str | None = Field(default=None, max_length=255)


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response (no password)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    is_active: bool
    created_at: datetime


class AuthResponse(BaseModel):
    """Combined auth response with user and token."""

    user: UserResponse
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Password reset response."""

    message: str = "If the email exists, a password reset link has been sent"
