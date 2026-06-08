import base64
import subprocess
from typing import Any

from rich.console import Console
from rich.text import Text

SHCHECK_TIMEOUT = 60


def run_shcheck(target: str) -> list[dict[str, Any]]:
    url = target if target.startswith("http") else f"https://{target}"
    result = subprocess.run(
        ["shcheck.py", "-d", url],
        capture_output=True,
        text=True,
        timeout=SHCHECK_TIMEOUT,
    )
    raw = (result.stdout + result.stderr).strip()

    console = Console(record=True, width=100, force_terminal=True)
    console.print(Text.from_ansi(raw))
    svg = console.export_svg(title=f"shcheck {url}")
    svg_b64 = base64.b64encode(svg.encode()).decode()

    return [{"url": url, "svg_b64": svg_b64}]
