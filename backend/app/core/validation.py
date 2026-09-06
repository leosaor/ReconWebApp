"""Validacao de alvos de recon.

Targets criados pelo usuario continuam sendo hostname ou IP. Alguns runners,
como headers e clickjacking, recebem URLs completas geradas pelo httpx e por
isso usam uma validacao separada para HTTP(S).
"""

import ipaddress
import re
import socket
from urllib.parse import urlparse

_MAX_TARGET_LEN = 253
_MAX_URL_LEN = 2048
_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata",
    "metadata.google.internal",
    "metadata.azure.internal",
    "instance-data",
}
_BLOCKED_HOSTNAME_SUFFIXES = (
    ".localhost",
    ".local",
)
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


def assert_public_target(value: str, *, resolve_dns: bool = True) -> None:
    """Bloqueia alvos internos, locais, metadata e hostnames que resolvem para IP nao publico."""
    host = _extract_host(value)
    if host is None:
        raise ValueError("Target deve ser um hostname, IP ou URL HTTP(S) valida")

    normalized = host.rstrip(".").lower()
    if normalized in _BLOCKED_HOSTNAMES or normalized.endswith(_BLOCKED_HOSTNAME_SUFFIXES):
        raise ValueError("Target interno/local nao permitido")

    direct_ip = _parse_ip(normalized)
    if direct_ip:
        _reject_non_public_ip(direct_ip)
        return

    if not resolve_dns:
        return

    for resolved_ip in _resolve_ips(normalized):
        _reject_non_public_ip(resolved_ip)


def is_public_target_allowed(value: str, *, resolve_dns: bool = True) -> bool:
    try:
        assert_public_target(value, resolve_dns=resolve_dns)
        return True
    except ValueError:
        return False


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


def _extract_host(value: str) -> str | None:
    candidate = value.strip()
    parsed = urlparse(candidate)
    if parsed.scheme:
        if parsed.scheme not in {"http", "https"}:
            return None
        return parsed.hostname
    return candidate


def _parse_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _reject_non_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if not ip.is_global:
        raise ValueError("Target resolve para IP interno/local nao permitido")


def _resolve_ips(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        records = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return []

    resolved: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    seen: set[str] = set()
    for record in records:
        raw_ip = record[4][0]
        if raw_ip in seen:
            continue
        seen.add(raw_ip)
        ip = _parse_ip(raw_ip)
        if ip:
            resolved.append(ip)
    return resolved
