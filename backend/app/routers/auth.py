"""
Auth router - admin login/token endpoints.
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.middleware.auth import hash_password, verify_password, create_access_token, create_refresh_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Admin login endpoint."""
    # Simple admin auth (in production use database)
    if request.email != settings.ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not verify_password(request.password, hash_password(settings.ADMIN_PASSWORD)):
        # Direct comparison for bootstrap
        if request.password != settings.ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

    token_data = {"sub": request.email, "role": "admin"}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
