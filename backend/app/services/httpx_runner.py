import json
import re
import subprocess
import tempfile
from collections.abc import Sequence
from typing import Any

_TARGET_RE = re.compile(
    r"^(https?://)?[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(:[0-9]{1,5})?$"
)
HTTPX_TIMEOUT = 300


def _validate_target(target: str) -> None:
    if not _TARGET_RE.match(target) or len(target) > 253:
        raise ValueError(f"Invalid target: {target!r}")


def run_httpx(target: str | Sequence[str]) -> list[dict[str, Any]]:
    targets = _normalize_targets(target)
    if not targets:
        return []

    command = [
        "httpx",
        "-json",
        "-silent",
        "-status-code",
        "-title",
        "-tech-detect",
        "-server",
        "-ip",
        "-cdn",
        "-location",
        "-response-time",
        "-content-length",
        "-content-type",
        "-probe",
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp.write("\n".join(targets) + "\n")
        tmp_path = tmp.name

    try:
        command[1:1] = ["-l", tmp_path]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=HTTPX_TIMEOUT,
        )
    finally:
        import os
        os.unlink(tmp_path)

    if result.returncode != 0:
        raise RuntimeError(f"httpx exited {result.returncode}: {result.stderr[:200]}")
    return [_parse_json_line(line) for line in result.stdout.splitlines() if line.strip()]


def _parse_json_line(line: str) -> dict[str, Any]:
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid httpx JSON output: {line[:200]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Invalid httpx JSON object: {line[:200]}")
    return parsed


def _normalize_targets(target: str | Sequence[str]) -> list[str]:
    raw_targets = [target] if isinstance(target, str) else list(target)
    targets = []
    seen = set()
    for raw_target in raw_targets:
        normalized = raw_target.strip()
        _validate_target(normalized)
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            targets.append(normalized)
    return targets
