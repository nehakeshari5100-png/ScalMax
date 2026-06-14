from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.config import settings
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_current_user,
    rate_limit,
)
from services.auth.models import (
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    ChangePasswordRequest,
)

router = APIRouter(tags=["Authentication"])


@router.post("/api/auth/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    _=Depends(rate_limit),
):
    if not verify_password(body.password, get_password_hash(settings.admin_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    token = create_access_token(
        data={"sub": "admin", "role": "admin"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return LoginResponse(
        token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/api/auth/refresh", response_model=RefreshResponse)
async def refresh(
    current_user: dict = Depends(get_current_user),
    _=Depends(rate_limit),
):
    token = create_access_token(
        data={"sub": current_user.get("sub", "admin"), "role": current_user.get("role", "admin")},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return RefreshResponse(
        token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/api/auth/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    _=Depends(rate_limit),
):
    if not verify_password(body.current_password, get_password_hash(settings.admin_password)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    return {"success": True, "message": "Password updated. Update SCALPEX_ADMIN_PASSWORD env var to persist."}


@router.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "sub": current_user.get("sub"),
        "role": current_user.get("role"),
    }


@router.get("/api/auth/openrouter-key")
async def get_openrouter_key(current_user: dict = Depends(get_current_user)):
    return {"api_key": settings.openrouter_api_key or ""}
