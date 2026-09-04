"""Validação de alvos de recon.

Garante que um alvo informado pelo usuário é um hostname ou IP sintaticamente
válido. O objetivo principal é cortar *argument injection* (valores começando
com `-` viram flags de CLI) e lixo óbvio na origem, antes que o valor chegue aos
runners que invocam subprocessos. Não impõe allowlist de escopo nem bloqueia
faixas internas — o controle de escopo é responsabilidade operacional.
"""

import ipaddress
import re

_MAX_TARGET_LEN = 253
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
        raise ValueError("Target inválido: vazio ou longo demais")
    if candidate.startswith("-"):
        raise ValueError("Target inválido: não pode começar com '-'")
    if is_valid_ip(candidate) or is_valid_hostname(candidate):
        return candidate
    raise ValueError("Target deve ser um hostname ou IP válido")
