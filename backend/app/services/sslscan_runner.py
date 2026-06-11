import base64
import re
import subprocess
from typing import Any

from rich.console import Console
from rich.text import Text

SSLSCAN_TIMEOUT = 180
_TARGET_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(:[0-9]{1,5})?$"
)


def _normalize_target(target: str) -> str:
    normalized = target.strip().removeprefix("https://").removeprefix("http://").split("/")[0]
    if not _TARGET_RE.match(normalized) or len(normalized) > 253:
        raise ValueError(f"Invalid target: {target!r}")
    return normalized


def _to_svg_b64(raw: str, title: str) -> str:
    console = Console(record=True, width=120, force_terminal=True)
    console.print(Text.from_ansi(raw))
    svg = console.export_svg(title=title)
    return base64.b64encode(svg.encode()).decode()


def run_sslscan(target: str) -> dict[str, Any]:
    normalized = _normalize_target(target)
    result = subprocess.run(
        ["sslscan", normalized],
        capture_output=True,
        text=True,
        timeout=SSLSCAN_TIMEOUT,
    )
    raw = (result.stdout + result.stderr).strip()
    if result.returncode != 0 and not raw:
        raise RuntimeError(f"sslscan exited {result.returncode}")

    return {
        "target": normalized,
        "command": f"sslscan {normalized}",
        "return_code": result.returncode,
        "raw": raw,
        "svg_b64": _to_svg_b64(raw, f"sslscan {normalized}"),
    }
