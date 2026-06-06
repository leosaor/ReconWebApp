import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.auth import ApiKeyCreated, LoginRequest, RegisterRequest, TokenResponse


def register_user(payload: RegisterRequest, db: Session, request: Request) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado")

    is_first_user = db.query(User).count() == 0
    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.ADMIN if is_first_user else UserRole.PENTESTER,
    )
    db.add(user)
    db.flush()
    _audit(db, user_id=user.id, action="user.register", entity="user", entity_id=str(user.id), request=request)
    db.commit()
    db.refresh(user)
    return user


def login_user(payload: LoginRequest, db: Session, request: Request) -> tuple[TokenResponse, str]:
    identifier = payload.identifier or payload.username or str(payload.email or "")
    user = _find_user_for_login(db, identifier)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    _audit(db, user_id=user.id, action="user.login", entity="user", entity_id=str(user.id), request=request)
    db.commit()
    return TokenResponse(access_token=access), refresh


def _find_user_for_login(db: Session, identifier: str) -> User | None:
    value = identifier.strip().lower()
    if not value:
        return None
    if "@" in value:
        return db.query(User).filter(sa.func.lower(User.email) == value).first()
    return (
        db.query(User)
        .filter(sa.func.lower(sa.func.split_part(User.email, "@", 1)) == value)
        .first()
    )


def create_api_key(name: str, user: User, db: Session, request: Request) -> ApiKeyCreated:
    raw_key, prefix, hashed_key = generate_api_key()
    key_obj = ApiKey(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name,
        prefix=prefix,
        hashed_key=hashed_key,
    )
    db.add(key_obj)
    db.flush()
    _audit(db, user_id=user.id, action="apikey.create", entity="api_key", entity_id=str(key_obj.id), request=request)
    db.commit()
    db.refresh(key_obj)
    return ApiKeyCreated(
        id=key_obj.id,
        name=key_obj.name,
        prefix=key_obj.prefix,
        raw_key=raw_key,
        created_at=key_obj.created_at,
    )


def revoke_api_key(key_id: uuid.UUID, user: User, db: Session, request: Request) -> None:
    key_obj = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.user_id == user.id,
        ApiKey.revoked.is_(False),
    ).first()
    if not key_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chave não encontrada")
    key_obj.revoked = True
    _audit(db, user_id=user.id, action="apikey.revoke", entity="api_key", entity_id=str(key_id), request=request)
    db.commit()


def _audit(
    db: Session,
    action: str,
    request: Request,
    user_id: uuid.UUID | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
) -> None:
    ip = request.client.host if request.client else None
    db.add(AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        ip_address=ip,
        created_at=datetime.now(timezone.utc),
    ))
