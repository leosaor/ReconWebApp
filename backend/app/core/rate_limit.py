"""Limiter compartilhado (slowapi) com storage no Redis existente.

O limiter é importado tanto pelo `main.py` (para registrar no app e no handler de
exceção) quanto pelas rotas que aplicam `@limiter.limit(...)`. Usa o IP do cliente
como chave; atrás do nginx, o `X-Forwarded-For` é repassado.
"""

from slowapi import Limiter
from starlette.requests import Request

from app.core.config import settings


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=settings.redis_url,
    default_limits=[],
)
