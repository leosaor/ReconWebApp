from datetime import datetime, timezone
from urllib.parse import urlparse

from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.scan import Scan, ScanStatus, ScanType
from app.models.scan_result import ScanResult
from app.services.artifacts import (
    content_fuzz_path,
    git_dumper_dir,
    git_dumper_summary_path,
    http_200_path,
    nuclei_scan_path,
    read_http_200_urls,
    read_target_subdomains,
    tls_scan_path,
    write_http_200_urls,
    write_target_subdomains,
    write_text_artifact,
)
from app.services.clickjacking_runner import run_clickjacking
from app.services.domain_spoofing_runner import run_domain_spoofing
from app.services.feroxbuster_runner import run_feroxbuster
from app.services.git_dumper_runner import run_git_dumper
from app.services.httpx_runner import run_httpx
from app.services.nmap_runner import run_nmap
from app.services.nuclei_runner import run_nuclei
from app.services.shcheck_runner import run_shcheck
from app.services.sslscan_runner import run_sslscan
from app.services.subfinder_runner import run_subfinder


def _mark_running(db, scan: Scan) -> None:
    scan.status = ScanStatus.RUNNING
    scan.started_at = datetime.now(timezone.utc)
    db.commit()


def _mark_completed(db, scan: Scan) -> None:
    scan.status = ScanStatus.COMPLETED
    scan.finished_at = datetime.now(timezone.utc)
    db.commit()


def _mark_failed(db, scan: Scan, error: str) -> None:
    scan.status = ScanStatus.FAILED
    scan.error = error[:500]
    scan.finished_at = datetime.now(timezone.utc)
    db.commit()


def _persist_results(db, scan: Scan, subdomains: list[str]) -> None:
    db.bulk_save_objects(
        [ScanResult(scan_id=scan.id, value=sub) for sub in subdomains]
    )
    db.commit()


def _persist_http_results(db, scan: Scan, results: list[dict]) -> None:
    db.bulk_save_objects(
        [
            ScanResult(
                scan_id=scan.id,
                value=result.get("url") or result.get("input") or scan.target.value,
                data=result,
            )
            for result in results
        ]
    )
    db.commit()


def _persist_port_results(db, scan: Scan, results: list[dict]) -> None:
    db.bulk_save_objects(
        [
            ScanResult(
                scan_id=scan.id,
                value=f"{result.get('host') or scan.target.value}:{result.get('port')}",
                data=result,
            )
            for result in results
        ]
    )
    db.commit()


def _aggregate_targets(db, scan: Scan) -> list[str]:
    """Alvo principal + subdominios descobertos em subdomain_enum concluidos."""
    artifact_subdomains = read_target_subdomains(scan.target)
    if artifact_subdomains is None:
        subdomains = [
            value
            for (value,) in (
                db.query(ScanResult.value)
                .join(Scan, ScanResult.scan_id == Scan.id)
                .filter(
                    Scan.target_id == scan.target_id,
                    Scan.scan_type == ScanType.SUBDOMAIN_ENUM,
                    Scan.status == ScanStatus.COMPLETED,
                )
                .order_by(ScanResult.created_at.asc())
                .all()
            )
        ]
    else:
        subdomains = artifact_subdomains

    targets = [scan.target.value]
    seen = {scan.target.value.lower()}
    for subdomain in subdomains:
        key = subdomain.lower()
        if key not in seen:
            seen.add(key)
            targets.append(subdomain)
    return targets


def _hosts_from_urls(urls: list[str]) -> list[str]:
    hosts: list[str] = []
    seen: set[str] = set()
    for url in urls:
        parsed = urlparse(url)
        host = parsed.hostname or urlparse(f"//{url}").hostname
        if not host:
            continue
        normalized = host.rstrip(".").lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            hosts.append(normalized)
    return hosts


def _tls_targets_from_urls(urls: list[str]) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    seen: set[str] = set()
    for url in urls:
        parsed = urlparse(url)
        if not parsed.hostname:
            parsed = urlparse(f"//{url}")
        if not parsed.hostname:
            continue

        host = parsed.hostname.rstrip(".").lower()
        target = f"{host}:{parsed.port}" if parsed.port else host
        key = target.lower()
        if key not in seen:
            seen.add(key)
            targets.append((target, url))
    return targets


def _http_200_urls_from_results(db, scan: Scan) -> list[str]:
    rows = (
        db.query(ScanResult)
        .join(Scan, ScanResult.scan_id == Scan.id)
        .filter(
            Scan.target_id == scan.target_id,
            Scan.scan_type == ScanType.HTTP_PROBE,
            Scan.status == ScanStatus.COMPLETED,
        )
        .order_by(ScanResult.created_at.asc())
        .all()
    )

    urls: list[str] = []
    seen: set[str] = set()
    for row in rows:
        data = row.data or {}
        if data.get("status_code") != 200:
            continue
        url = str(data.get("url") or row.value).strip()
        key = url.lower()
        if url and key not in seen:
            seen.add(key)
            urls.append(url)
    return urls


def _http_200_urls_for_scan(db, scan: Scan) -> list[str] | None:
    http_200_urls = read_http_200_urls(scan.target)
    if http_200_urls:
        return http_200_urls

    result_urls = _http_200_urls_from_results(db, scan)
    if result_urls:
        write_http_200_urls(scan.target, result_urls)
        return result_urls

    return http_200_urls


@celery_app.task(name="recon.run_subdomain_enum", bind=True)
def run_subdomain_enum(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        domain = scan.target.value
        subdomains = run_subfinder(domain)
        _persist_results(db, scan, subdomains)
        subdomains_file = write_target_subdomains(scan.target, subdomains)
        _mark_completed(db, scan)
        return {"scan_id": scan_id, "found": len(subdomains), "file": str(subdomains_file)}
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_port_scan", bind=True)
def run_port_scan(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        http_200_urls = _http_200_urls_for_scan(db, scan)
        if http_200_urls is None:
            raise RuntimeError("Arquivo http-200.txt nao encontrado. Execute o HTTP Probe antes do Port Scan.")

        if not http_200_urls:
            raise RuntimeError("Nenhum HTTP 200 original encontrado pelo HTTP Probe para usar no Port Scan.")

        targets = _hosts_from_urls(http_200_urls)
        if not targets:
            raise RuntimeError("Nenhum host valido encontrado no http-200.txt para o Port Scan.")

        results = run_nmap(targets, use_input_file=True)
        _persist_port_results(db, scan, results)
        _mark_completed(db, scan)
        return {"scan_id": scan_id, "targets": len(targets), "found": len(results)}
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_http_probe", bind=True)
def run_http_probe(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        targets = _aggregate_targets(db, scan)
        results = run_httpx(targets)
        http_200_results = run_httpx(targets, match_code="200")
        output_file = write_http_200_urls(
            scan.target,
            [str(result.get("url")) for result in http_200_results if result.get("url")],
        )
        _persist_http_results(db, scan, results)
        _mark_completed(db, scan)
        return {
            "scan_id": scan_id,
            "targets": len(targets),
            "found": len(results),
            "found_200": len(http_200_results),
            "file": str(output_file),
        }
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_header_check", bind=True)
def run_header_check(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        http_200_urls = _http_200_urls_for_scan(db, scan)
        if http_200_urls is None:
            raise RuntimeError("Arquivo http-200.txt nao encontrado. Execute o HTTP Probe antes do Header Check.")
        if not http_200_urls:
            raise RuntimeError("Nenhum HTTP 200 original encontrado pelo HTTP Probe para usar no Header Check.")

        results = []
        for url in http_200_urls:
            results.extend(run_shcheck(url))
        db.bulk_save_objects(
            [ScanResult(scan_id=scan.id, value=r["url"], data=r) for r in results]
        )
        db.commit()
        _mark_completed(db, scan)
        return {"scan_id": scan_id, "found": len(results)}
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_clickjacking", bind=True)
def run_clickjacking_task(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        http_200_urls = _http_200_urls_for_scan(db, scan)
        if http_200_urls is None:
            raise RuntimeError("Arquivo http-200.txt nao encontrado. Execute o HTTP Probe antes do Clickjacking.")
        if not http_200_urls:
            raise RuntimeError("Nenhum HTTP 200 original encontrado pelo HTTP Probe para usar no Clickjacking.")

        results = []
        for url in http_200_urls:
            results.extend(run_clickjacking(url))
        db.bulk_save_objects(
            [ScanResult(scan_id=scan.id, value=r["url"], data=r) for r in results]
        )
        db.commit()
        _mark_completed(db, scan)
        return {"scan_id": scan_id, "found": len(results)}
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_domain_spoofing", bind=True)
def run_domain_spoofing_task(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        results = run_domain_spoofing(scan.target.value)
        db.bulk_save_objects(
            [ScanResult(scan_id=scan.id, value=r["check"], data=r) for r in results]
        )
        db.commit()
        _mark_completed(db, scan)
        return {"scan_id": scan_id, "found": len(results)}
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_content_fuzz", bind=True)
def run_content_fuzz(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        http_200_urls = _http_200_urls_for_scan(db, scan)
        if http_200_urls is None:
            raise RuntimeError("Arquivo http-200.txt nao encontrado. Execute o HTTP Probe antes do Fuzzing.")
        if not http_200_urls:
            raise RuntimeError("Nenhum HTTP 200 original encontrado pelo HTTP Probe para usar no Fuzzing.")

        input_file = http_200_path(scan.target)
        output_file = content_fuzz_path(scan.target)
        results = run_feroxbuster(input_file, output_file)

        for result in results:
            result["output_file"] = str(output_file)

        db.bulk_save_objects(
            [ScanResult(scan_id=scan.id, value=result["url"], data=result) for result in results]
        )
        db.commit()
        _mark_completed(db, scan)
        return {
            "scan_id": scan_id,
            "targets": len(http_200_urls),
            "found": len(results),
            "file": str(output_file),
        }
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_git_dump", bind=True)
def run_git_dump(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        http_200_urls = _http_200_urls_for_scan(db, scan)
        if http_200_urls is None:
            raise RuntimeError("Arquivo http-200.txt nao encontrado. Execute o HTTP Probe antes do Git Dumper.")
        if not http_200_urls:
            raise RuntimeError("Nenhum HTTP 200 original encontrado pelo HTTP Probe para usar no Git Dumper.")

        output_dir = git_dumper_dir(scan.target)
        results = run_git_dumper(http_200_urls, output_dir)
        summary_lines = []
        for result in results:
            result["output_dir"] = str(output_dir)
            status = "VULNERAVEL" if result["vulnerable"] else "nao vulneravel"
            summary_lines.append(f"[{status}] {result['git_url']} -> {result.get('dump_dir') or '-'}")

        summary_file = write_text_artifact(
            git_dumper_summary_path(scan.target),
            "\n".join(summary_lines) + ("\n" if summary_lines else ""),
        )
        for result in results:
            result["summary_file"] = str(summary_file)

        db.bulk_save_objects(
            [ScanResult(scan_id=scan.id, value=result["url"], data=result) for result in results]
        )
        db.commit()
        _mark_completed(db, scan)
        return {
            "scan_id": scan_id,
            "targets": len(http_200_urls),
            "found": sum(1 for result in results if result["vulnerable"]),
            "file": str(summary_file),
        }
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_nuclei_scan", bind=True)
def run_nuclei_scan(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        output_file = nuclei_scan_path(scan.target)
        results = run_nuclei(scan.target.value, output_file)
        for result in results:
            result["output_file"] = str(output_file)

        db.bulk_save_objects(
            [
                ScanResult(
                    scan_id=scan.id,
                    value=str(result.get("matched_at") or result.get("host") or scan.target.value),
                    data=result,
                )
                for result in results
            ]
        )
        db.commit()
        _mark_completed(db, scan)
        return {
            "scan_id": scan_id,
            "targets": 1,
            "found": len(results),
            "file": str(output_file),
        }
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="recon.run_tls_scan", bind=True)
def run_tls_scan(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        http_200_urls = _http_200_urls_for_scan(db, scan)
        if http_200_urls is None:
            raise RuntimeError("Arquivo http-200.txt nao encontrado. Execute o HTTP Probe antes do TLS/Cifras.")
        if not http_200_urls:
            raise RuntimeError("Nenhum HTTP 200 original encontrado pelo HTTP Probe para usar no TLS/Cifras.")

        tls_targets = _tls_targets_from_urls(http_200_urls)
        if not tls_targets:
            raise RuntimeError("Nenhum host valido encontrado no http-200.txt para o TLS/Cifras.")

        results = []
        raw_outputs = []
        for target, source_url in tls_targets:
            result = run_sslscan(target)
            result["source_url"] = source_url
            results.append(result)
            raw_outputs.append(f"### {target} ({source_url})\n{result['raw']}")

        output_file = write_text_artifact(tls_scan_path(scan.target), "\n\n".join(raw_outputs))
        for result in results:
            result["output_file"] = str(output_file)
        db.bulk_save_objects(
            [ScanResult(scan_id=scan.id, value=result["target"], data=result) for result in results]
        )
        db.commit()
        _mark_completed(db, scan)
        return {"scan_id": scan_id, "found": len(results), "file": str(output_file)}
    except SoftTimeLimitExceeded:
        if scan:
            _mark_failed(db, scan, "timeout")
        raise
    except Exception as exc:  # noqa: BLE001
        if scan:
            _mark_failed(db, scan, str(exc))
        raise
    finally:
        db.close()
