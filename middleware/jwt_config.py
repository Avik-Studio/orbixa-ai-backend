"""
JWT Middleware configuration for Orbixa AI Agent OS.
Configures JWT authentication using Agno's built-in middleware.
Extracts userId from JWT.
"""
import os
from agno.os.middleware import JWTMiddleware


def create_jwt_middleware() -> JWTMiddleware:
    """Create and configure JWT middleware for authentication."""
    jwt_secret = os.getenv("JWT_SECRET")
    
    return JWTMiddleware(
        secret_key=jwt_secret,
        algorithm="HS256",
        user_id_claim="userId",  # Extracts to run_context.user_id
        dependencies_claims=["userId"],  # Extract userId for dependencies
        validate=True,
        excluded_route_paths=[
            "/",
            "/health",
            "/v1/health",
            "/v1",
            "/docs",
            "/openapi.json",
            "/redoc"
        ],
    )
