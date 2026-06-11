from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.target import Target


def target_artifact_dir(target: "Target") -> Path:
    return (
        Path(settings.recon_output_dir)
        / "projects"
        / str(target.project_id)
        / "targets"
        / str(target.id)
    )


def subdomains_path(target: "Target") -> Path:
    return target_artifact_dir(target) / "subdomains.txt"


def tls_scan_path(target: "Target") -> Path:
    return target_artifact_dir(target) / "tls-scan.txt"


def content_fuzz_path(target: "Target") -> Path:
    return target_artifact_dir(target) / "feroxbuster.txt"


def git_dumper_dir(target: "Target") -> Path:
    return target_artifact_dir(target) / "git-dumper"


def git_dumper_summary_path(target: "Target") -> Path:
    return target_artifact_dir(target) / "git-dumper.txt"


def nuclei_scan_path(target: "Target") -> Path:
    return target_artifact_dir(target) / "nuclei.txt"


def http_200_path(target: "Target") -> Path:
    return target_artifact_dir(target) / "http-200.txt"


def write_text_artifact(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)
    return path


def write_target_subdomains(target: "Target", subdomains: list[str]) -> Path:
    path = subdomains_path(target)

    seen: set[str] = set()
    unique_subdomains: list[str] = []
    for subdomain in subdomains:
        normalized = subdomain.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            unique_subdomains.append(normalized)

    write_text_artifact(
        path,
        "".join(f"{subdomain}\n" for subdomain in unique_subdomains),
    )
    return path


def read_target_subdomains(target: "Target") -> list[str] | None:
    path = subdomains_path(target)
    if not path.exists():
        return None

    subdomains: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        subdomain = line.strip()
        key = subdomain.lower()
        if subdomain and key not in seen:
            seen.add(key)
            subdomains.append(subdomain)
    return subdomains


def write_http_200_urls(target: "Target", urls: list[str]) -> Path:
    path = http_200_path(target)
    seen: set[str] = set()
    unique_urls: list[str] = []
    for url in urls:
        normalized = url.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            unique_urls.append(normalized)

    write_text_artifact(path, "".join(f"{url}\n" for url in unique_urls))
    return path


def read_http_200_urls(target: "Target") -> list[str] | None:
    path = http_200_path(target)
    if not path.exists():
        return None

    urls: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        url = line.strip()
        key = url.lower()
        if url and key not in seen:
            seen.add(key)
            urls.append(url)
    return urls
