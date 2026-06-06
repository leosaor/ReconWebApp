import json
import re
import subprocess
from typing import Any

_TARGET_RE = re.compile(
    r"^(https?://)?[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(:[0-9]{1,5})?$"
)
HTTPX_TIMEOUT = 300


def _validate_target(target: str) -> None:
    if not _TARGET_RE.match(target) or len(target) > 253:
        raise ValueError(f"Invalid target: {target!r}")


def run_httpx(target: str) -> list[dict[str, Any]]:
    _validate_target(target)
    result = subprocess.run(
        [
            "httpx",
            "-u",
            target,
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
        ],
        capture_output=True,
        text=True,
        timeout=HTTPX_TIMEOUT,
    )
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
