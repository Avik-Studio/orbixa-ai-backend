"""
Auth utilities — password hashing, JWT creation, Google token verification.
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
import bcrypt
import httpx


JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


# ── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ──────────────────────────────────────────────────────────────

def create_access_token(user_id: str, extra: Optional[dict] = None) -> str:
    payload = {
        "userId": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_reset_token() -> str:
    """Generate a URL-safe random token for password resets."""
    return secrets.token_urlsafe(32)


# ── Google ID-token verification ─────────────────────────────────────────────

async def verify_google_id_token(id_token: str) -> Optional[dict]:
    """
    Verify a Google ID token via Google's tokeninfo endpoint.
    Returns the decoded payload dict on success, or None on failure.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"id_token": id_token},
        )
    if resp.status_code != 200:
        return None

    payload = resp.json()

    # Verify the audience matches our client ID
    if GOOGLE_CLIENT_ID and payload.get("aud") != GOOGLE_CLIENT_ID:
        return None

    return payload
