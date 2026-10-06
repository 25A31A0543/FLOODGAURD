"""
FloodGuard Step 5: Security API helpers
OAuth2-compatible token generation and validation endpoints.
"""
from fastapi import APIRouter

from floodguard.middleware.auth import create_access_token, decode_access_token

security_router = APIRouter(prefix="/api/v1/auth", tags=["Security"])


@security_router.post("/token", summary="Step 5: Generate Authority Access Token")
async def generate_token(username: str = "authority_user", role: str = "authority"):
    """
    Generate a JWT Bearer token for authority dashboard access.
    In production, integrate with your IdP (Keycloak, Auth0, etc.).
    """
    token = create_access_token(subject=username, role=role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": "authority:read authority:write alert:dispatch",
        "platform": "FloodGuard AI — Step 5: Integration & Scaling",
    }


@security_router.get("/verify", summary="Step 5: Verify Token Validity")
async def verify_token(token: str):
    """Validate a Bearer token and return its payload claims."""
    payload = decode_access_token(token)
    return {
        "valid": True,
        "subject": payload.get("sub"),
        "role": payload.get("role"),
        "issued_at": payload.get("iat"),
        "expires_at": payload.get("exp"),
    }
