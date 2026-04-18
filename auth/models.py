"""
User models and Pydantic schemas for Orbixa AI authentication.
"""
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Request Schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_REGEX.match(v):
            raise ValueError("Invalid email address")
        return v.lower()


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_REGEX.match(v):
            raise ValueError("Invalid email address")
        return v.lower()


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_REGEX.match(v):
            raise ValueError("Invalid email address")
        return v.lower()


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class GoogleAuthRequest(BaseModel):
    id_token: str


# ── Response Schemas ─────────────────────────────────────────────────────────

class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None


# ── Database Document Shape ──────────────────────────────────────────────────

def new_user_doc(name: str, email: str, hashed_password: str, provider: str = "local") -> dict:
    """Return a dict ready to insert into MongoDB `users` collection."""
    return {
        "name": name,
        "email": email,
        "password": hashed_password,
        "provider": provider,          # "local" | "google"
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "reset_token": None,
        "reset_token_expires": None,
    }
