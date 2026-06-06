from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token, hash_api_key
from app.db.session import get_db
from app.models.api_key import ApiKey
from app.models.user import User, UserRole

_bearer = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    api_key: str | None = Security(_api_key_header),
) -> User:
    user = _user_from_jwt(credentials, db) or _user_from_api_key(api_key, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return user


def _user_from_jwt(
    credentials: HTTPAuthorizationCredentials | None, db: Session
) -> User | None:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user = db.get(User, payload["sub"])
        if user and user.is_active:
            return user
    except jwt.InvalidTokenError:
        pass
    return None


def _user_from_api_key(raw_key: str | None, db: Session) -> User | None:
    if not raw_key:
        return None
    hashed = hash_api_key(raw_key)
    key_obj = (
        db.query(ApiKey).filter(ApiKey.hashed_key == hashed, ApiKey.revoked.is_(False)).first()
    )
    if not key_obj or not key_obj.user.is_active:
        return None
    key_obj.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return key_obj.user


def require_writer(user: User = Depends(get_current_user)) -> User:
    if user.role == UserRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return user

