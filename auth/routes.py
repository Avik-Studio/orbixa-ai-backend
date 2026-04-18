"""
Authentication routes for Orbixa AI.
Endpoints: register, login, forgot-password, reset-password, google-auth.
"""
import os
import logging
from datetime import datetime, timedelta

import certifi
import jwt
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from pymongo import MongoClient

from auth.models import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GoogleAuthRequest,
    AuthResponse,
    new_user_doc,
)
from auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_reset_token,
    verify_google_id_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── MongoDB connection (same DB as the agent, separate collection) ───────────

_mongo_client: MongoClient | None = None


def _get_users_col():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(
            os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            tlsCAFile=certifi.where(),
        )
    db = _mongo_client[os.getenv("MONGODB_DATABASE", "Orbixa-AI")]
    return db["users"]


# ── POST /auth/register ─────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    col = _get_users_col()

    if col.find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(body.password)
    doc = new_user_doc(name=body.name, email=body.email, hashed_password=hashed)
    result = col.insert_one(doc)
    user_id = str(result.inserted_id)

    token = create_access_token(user_id, extra={"email": body.email, "name": body.name})

    logger.info(f"New user registered: {body.email}")
    return AuthResponse(
        success=True,
        message="Registration successful",
        token=token,
        user={"id": user_id, "name": body.name, "email": body.email},
    )


# ── POST /auth/login ────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    col = _get_users_col()
    user = col.find_one({"email": body.email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.get("provider") == "google" and not user.get("password"):
        raise HTTPException(
            status_code=401,
            detail="This account uses Google sign-in. Please log in with Google.",
        )

    if not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token(user_id, extra={"email": user["email"], "name": user["name"]})

    logger.info(f"User logged in: {body.email}")
    return AuthResponse(
        success=True,
        message="Login successful",
        token=token,
        user={"id": user_id, "name": user["name"], "email": user["email"]},
    )


# ── POST /auth/forgot-password ──────────────────────────────────────────────

@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(body: ForgotPasswordRequest):
    col = _get_users_col()
    user = col.find_one({"email": body.email})

    # Always return success to avoid email-enumeration attacks
    if not user:
        return AuthResponse(success=True, message="If that email exists, a reset link has been sent.")

    if user.get("provider") == "google" and not user.get("password"):
        return AuthResponse(success=True, message="If that email exists, a reset link has been sent.")

    reset_token = create_reset_token()
    col.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_token": reset_token,
                "reset_token_expires": datetime.utcnow() + timedelta(hours=1),
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # TODO: Send email with reset link containing `reset_token`
    # For now, return the token in the response (dev only).
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    logger.info(f"Password reset requested for {body.email} — link: {reset_link}")

    return AuthResponse(
        success=True,
        message="If that email exists, a reset link has been sent.",
        # Remove the token from production responses — only for dev/testing
        token=reset_token if os.getenv("DEBUG", "False").lower() == "true" else None,
    )


# ── POST /auth/reset-password ───────────────────────────────────────────────

@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(body: ResetPasswordRequest):
    col = _get_users_col()
    user = col.find_one({
        "reset_token": body.token,
        "reset_token_expires": {"$gt": datetime.utcnow()},
    })

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    hashed = hash_password(body.new_password)
    col.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hashed,
                "reset_token": None,
                "reset_token_expires": None,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    logger.info(f"Password reset completed for {user['email']}")
    return AuthResponse(success=True, message="Password has been reset successfully")


# ── POST /auth/google ────────────────────────────────────────────────────────

@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest):
    payload = await verify_google_id_token(body.id_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    email = payload.get("email")
    name = payload.get("name", email.split("@")[0] if email else "User")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    col = _get_users_col()
    user = col.find_one({"email": email})

    if user:
        # Existing user — update provider if needed, issue token
        if user.get("provider") != "google":
            col.update_one(
                {"_id": user["_id"]},
                {"$set": {"provider": "google", "updated_at": datetime.utcnow()}},
            )
        user_id = str(user["_id"])
    else:
        # New user via Google — create account (no password)
        doc = new_user_doc(name=name, email=email, hashed_password="", provider="google")
        result = col.insert_one(doc)

        user_id = str(result.inserted_id)
        logger.info(f"New Google user registered: {email}")

    token = create_access_token(user_id, extra={"email": email, "name": name})

    return AuthResponse(
        success=True,
        message="Google authentication successful",
        token=token,
        user={"id": user_id, "name": name, "email": email},
    )


# ── GET /auth/me ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=AuthResponse)
async def get_me(request: Request):
    """Return the currently authenticated user's profile from their JWT."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ", 1)[1]
    secret = os.getenv("JWT_SECRET", "")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    col = _get_users_col()
    try:
        user = col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return AuthResponse(
        success=True,
        message="Authenticated",
        token=None,
        user={"id": user_id, "name": user["name"], "email": user["email"]},
    )
