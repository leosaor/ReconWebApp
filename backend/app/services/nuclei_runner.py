import subprocess
from pathlib import Path
from typing import Any

NUCLEI_TIMEOUT = 1200


def run_nuclei(target: str, output_file: Path) -> list[dict[str, Any]]:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.unlink(missing_ok=True)

    command = ["nuclei", "-u", target, "-o", str(output_file)]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=NUCLEI_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        output = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
        if output.strip():
            return [_normalize_line(line) for line in output.splitlines() if line.strip()]
        raise RuntimeError(f"nuclei excedeu {NUCLEI_TIMEOUT} segundos sem gerar resultados") from exc

    output = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
    if result.returncode != 0 and not output.strip():
        raise RuntimeError(f"nuclei exited {result.returncode}: {result.stderr[:300]}")

    return [_normalize_line(line) for line in output.splitlines() if line.strip()]


def _normalize_line(line: str) -> dict[str, Any]:
    parts = line.split()
    template_id = _strip_brackets(parts[0]) if len(parts) > 0 else None
    protocol = _strip_brackets(parts[1]) if len(parts) > 1 else None
    severity = _strip_brackets(parts[2]) if len(parts) > 2 else None
    matched_at = next((part for part in reversed(parts) if part.startswith(("http://", "https://"))), None)
    return {
        "template_id": template_id,
        "name": template_id,
        "severity": severity,
        "type": protocol,
        "matched_at": matched_at,
        "raw": line,
    }


def _strip_brackets(value: str) -> str:
    return value.strip("[]")
