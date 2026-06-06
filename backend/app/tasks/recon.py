from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.scan import Scan, ScanStatus, ScanType
from app.models.scan_result import ScanResult
from app.services.httpx_runner import run_httpx
from app.services.nmap_runner import run_nmap
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


def _http_probe_targets(db, scan: Scan) -> list[str]:
    subdomains = (
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

    targets = [scan.target.value]
    seen = {scan.target.value.lower()}
    for (subdomain,) in subdomains:
        key = subdomain.lower()
        if key not in seen:
            seen.add(key)
            targets.append(subdomain)
    return targets


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
        _mark_completed(db, scan)
        return {"scan_id": scan_id, "found": len(subdomains)}
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
        results = run_nmap(scan.target.value)
        _persist_port_results(db, scan, results)
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


@celery_app.task(name="recon.run_http_probe", bind=True)
def run_http_probe(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        targets = _http_probe_targets(db, scan)
        results = run_httpx(targets)
        _persist_http_results(db, scan, results)
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
