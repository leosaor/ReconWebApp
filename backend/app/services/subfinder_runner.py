import re
import subprocess

_HOSTNAME_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$")
SUBFINDER_TIMEOUT = 300


def _validate_domain(domain: str) -> None:
    if not _HOSTNAME_RE.match(domain) or len(domain) > 253:
        raise ValueError(f"Invalid domain: {domain!r}")


def run_subfinder(domain: str) -> list[str]:
    _validate_domain(domain)
    result = subprocess.run(
        ["subfinder", "-d", domain, "-silent"],
        capture_output=True,
        text=True,
        timeout=SUBFINDER_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"subfinder exited {result.returncode}: {result.stderr[:200]}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
