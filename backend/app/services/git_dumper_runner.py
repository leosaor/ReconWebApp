import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

GIT_DUMPER_TIMEOUT = 180
GIT_DUMPER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36"
)


def run_git_dumper(urls: list[str], output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for url in urls:
        normalized_url = url.strip().rstrip("/")
        if not normalized_url:
            continue

        git_url = f"{normalized_url}/.git"
        dump_dir = output_dir / _safe_dir_name(normalized_url)
        if dump_dir.exists():
            shutil.rmtree(dump_dir)

        try:
            result = subprocess.run(
                [
                    "git-dumper",
                    "-j",
                    "10",
                    "-r",
                    "2",
                    "-t",
                    "15",
                    "-u",
                    GIT_DUMPER_USER_AGENT,
                    git_url,
                    str(dump_dir),
                ],
                capture_output=True,
                text=True,
                timeout=GIT_DUMPER_TIMEOUT,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("git-dumper nao encontrado no ambiente do worker") from exc
        except subprocess.TimeoutExpired:
            results.append(
                {
                    "url": normalized_url,
                    "git_url": git_url,
                    "vulnerable": False,
                    "return_code": "timeout",
                    "dump_dir": None,
                    "raw": f"Timeout apos {GIT_DUMPER_TIMEOUT} segundos",
                }
            )
            continue

        raw = (result.stdout + result.stderr).strip()
        vulnerable = result.returncode == 0 and (dump_dir / ".git").exists()
        results.append(
            {
                "url": normalized_url,
                "git_url": git_url,
                "vulnerable": vulnerable,
                "return_code": result.returncode,
                "dump_dir": str(dump_dir) if vulnerable else None,
                "raw": raw[:4000],
            }
        )

    return results


def _safe_dir_name(url: str) -> str:
    value = re.sub(r"^https?://", lambda match: f"{match.group(0)[:-3]}_", url, flags=re.IGNORECASE)
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("._-")
    return value[:120] or "target"
