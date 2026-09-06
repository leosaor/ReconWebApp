"""Validacao de alvos de recon.

Targets criados pelo usuario continuam sendo hostname ou IP. Alguns runners,
como headers e clickjacking, recebem URLs completas geradas pelo httpx e por
isso usam uma validacao separada para HTTP(S).
"""

import ipaddress
import re
from urllib.parse import urlparse

_MAX_TARGET_LEN = 253
_MAX_URL_LEN = 2048
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
)


def is_valid_hostname(value: str) -> bool:
    return bool(_HOSTNAME_RE.match(value))


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def validate_target_value(value: str) -> str:
    """Retorna o alvo normalizado ou levanta ValueError."""
    candidate = value.strip()
    if not candidate or len(candidate) > _MAX_TARGET_LEN:
        raise ValueError("Target invalido: vazio ou longo demais")
    if candidate.startswith("-"):
        raise ValueError("Target invalido: nao pode comecar com '-'")
    if is_valid_ip(candidate) or is_valid_hostname(candidate):
        return candidate
    raise ValueError("Target deve ser um hostname ou IP valido")


def validate_target_url_or_value(value: str) -> str:
    """Aceita hostname/IP ou URL HTTP(S), validando o host."""
    candidate = value.strip()
    if not candidate or len(candidate) > _MAX_URL_LEN:
        raise ValueError("Target invalido: vazio ou longo demais")
    if candidate.startswith("-"):
        raise ValueError("Target invalido: nao pode comecar com '-'")

    parsed = urlparse(candidate)
    if not parsed.scheme:
        return validate_target_value(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Target deve ser um hostname, IP ou URL HTTP(S) valida")
    if is_valid_ip(parsed.hostname) or is_valid_hostname(parsed.hostname):
        return candidate
    raise ValueError("Target deve ser um hostname, IP ou URL HTTP(S) valida")
