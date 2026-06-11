import subprocess
from pathlib import Path
from typing import Any

FEROXBUSTER_TIMEOUT = 600
FEROXBUSTER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36"
)
BASIC_WORDLIST_PATH = Path(__file__).resolve().parents[1] / "wordlists" / "basic-fuzz.txt"


def run_feroxbuster(input_file: Path, output_file: Path) -> list[dict[str, Any]]:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.unlink(missing_ok=True)

    with input_file.open("r", encoding="utf-8") as stdin:
        result = subprocess.run(
            [
                "feroxbuster",
                "--stdin",
                "--no-state",
                "-a",
                FEROXBUSTER_USER_AGENT,
                "-w",
                str(BASIC_WORDLIST_PATH),
                "-s",
                "200",
                "-k",
                "-q",
                "-n",
                "-o",
                str(output_file),
            ],
            stdin=stdin,
            capture_output=True,
            text=True,
            timeout=FEROXBUSTER_TIMEOUT,
        )

    output = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
    if result.returncode != 0 and not output.strip():
        raise RuntimeError(f"feroxbuster exited {result.returncode}: {result.stderr[:200]}")

    return [_normalize_result(item) for item in _parse_text_lines(output)]


def _parse_text_lines(output: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split()
        url = next((part for part in reversed(parts) if part.startswith(("http://", "https://"))), None)
        if not url:
            continue
        results.append(
            {
                "url": url,
                "status_code": _first_int(parts, suffix=None),
                "lines": _first_int(parts, suffix="l"),
                "words": _first_int(parts, suffix="w"),
                "content_length": _first_int(parts, suffix="c"),
                "raw": line,
            }
        )
    return results


def _normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    status = result.get("status_code")
    return {
        "url": result.get("url"),
        "status_code": int(status) if str(status).isdigit() else status,
        "content_length": result.get("content_length"),
        "words": result.get("words"),
        "lines": result.get("lines"),
        "redirect": None,
        "raw": result,
    }


def _first_int(parts: list[str], suffix: str | None) -> int | None:
    for part in parts:
        candidate = part[:-1] if suffix and part.endswith(suffix) else part
        if suffix and not part.endswith(suffix):
            continue
        if candidate.isdigit():
            return int(candidate)
    return None
