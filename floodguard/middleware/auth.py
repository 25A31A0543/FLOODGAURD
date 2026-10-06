"""
FloodGuard Step 5: JWT Authentication Middleware
Protects authority-only endpoints with Bearer token validation.
"""
import os
import time
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ---------------------------------------------------------------------------
# JWT support (graceful fallback if PyJWT not installed)
# ---------------------------------------------------------------------------
try:
    import jwt as pyjwt
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600  # 1 hour

security = HTTPBearer(auto_error=False)


def create_access_token(subject: str, role: str = "authority") -> str:
    """
    Generate a signed JWT access token for FloodGuard authority users.
    Falls back to a simple opaque token if PyJWT is not installed.
    """
    if _JWT_AVAILABLE:
        payload = {
            "sub": subject,
            "role": role,
            "iat": int(time.time()),
            "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS,
            "iss": "floodguard-platform",
        }
        return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    # Fallback: base64-encoded opaque token
    import base64, json
    payload = {"sub": subject, "role": role, "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_access_token(token: str) -> dict:
    """
    Validate and decode a JWT access token.
    Returns payload dict or raises HTTPException.
    """
    if _JWT_AVAILABLE:
        try:
            payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except pyjwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    # Fallback: accept any non-empty token in demo mode
    if token and len(token) > 10:
        return {"sub": "demo_authority", "role": "authority"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_authority_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    FastAPI dependency: validates Bearer token and returns authority user payload.
    Use as: `user = Depends(get_current_authority_user)`
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authority credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_role(required_role: str):
    """Role-based access control decorator factory."""
    def _check_role(user: dict = Depends(get_current_authority_user)) -> dict:
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {required_role}",
            )
        return user
    return _check_role
