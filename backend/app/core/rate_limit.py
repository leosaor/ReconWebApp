"""Limiter compartilhado (slowapi) com storage no Redis existente.

O limiter é importado tanto pelo `main.py` (para registrar no app e no handler de
exceção) quanto pelas rotas que aplicam `@limiter.limit(...)`. Usa o IP do cliente
como chave; atrás do nginx, o `X-Forwarded-For` é repassado.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    default_limits=[],
)
