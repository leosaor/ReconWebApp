from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.scan import Scan, ScanStatus
from app.models.scan_result import ScanResult
from app.services.httpx_runner import run_httpx
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


@celery_app.task(name="recon.run_http_probe", bind=True)
def run_http_probe(self, scan_id: str) -> dict:
    db = SessionLocal()
    scan = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return {"scan_id": scan_id, "status": "missing"}

        _mark_running(db, scan)
        results = run_httpx(scan.target.value)
        _persist_http_results(db, scan, results)
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
