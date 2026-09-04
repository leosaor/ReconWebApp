import uuid

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.security import create_access_token, decode_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_ACCESS_COOKIE = "access_token"
_REFRESH_MAX_AGE = 7 * 24 * 3600
_ACCESS_MAX_AGE = settings.access_token_expire_minutes * 60


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(
    payload: RegisterRequest, request: Request, db: Session = Depends(get_db)
) -> RegisterResponse:
    message = auth_service.register_user(payload, db, request)
    return RegisterResponse(message=message)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    token_response, refresh = auth_service.login_user(payload, db, request)
    _set_auth_cookies(response, token_response.access_token, refresh)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> TokenResponse:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token ausente")
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        access_token = create_access_token(payload["sub"])
        response.set_cookie(
            key=_ACCESS_COOKIE,
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=_ACCESS_MAX_AGE,
            secure=settings.cookie_secure,
        )
        return TokenResponse(access_token=access_token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(_REFRESH_COOKIE)
    response.delete_cookie(_ACCESS_COOKIE)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiKeyCreated:
    return auth_service.create_api_key(payload.name, current_user, db, request)


@router.get("/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    from app.models.api_key import ApiKey

    return db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    auth_service.revoke_api_key(key_id, current_user, db, request)


def _set_auth_cookies(response: Response, access_token: str, refresh: str) -> None:
    response.set_cookie(
        key=_ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=_ACCESS_MAX_AGE,
        secure=settings.cookie_secure,
    )
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh,
        httponly=True,
        samesite="lax",
        max_age=_REFRESH_MAX_AGE,
        secure=settings.cookie_secure,
    )
