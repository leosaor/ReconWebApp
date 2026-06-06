import uuid
from unittest.mock import patch

import pytest

from app.models.scan import Scan, ScanStatus, ScanType
from app.models.scan_result import ScanResult
from app.tasks.recon import run_subdomain_enum
from tests.factories import make_project, make_target, make_user


def _make_pending_scan(db):
    user = make_user(db, f"worker-{uuid.uuid4()}@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)
    scan = Scan(
        target_id=target.id,
        scan_type=ScanType.SUBDOMAIN_ENUM,
        status=ScanStatus.PENDING,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def test_task_sucesso_completa_scan_e_persiste_resultados(db):
    scan = _make_pending_scan(db)

    with patch("app.tasks.recon.run_subfinder", return_value=["api.example.com"]):
        with patch("app.tasks.recon.SessionLocal", return_value=db):
            with patch.object(db, "close", return_value=None):
                result = run_subdomain_enum.__wrapped__(str(scan.id))

    db.refresh(scan)
    results = db.query(ScanResult).filter(ScanResult.scan_id == scan.id).all()
    assert result == {"scan_id": str(scan.id), "found": 1}
    assert scan.status == ScanStatus.COMPLETED
    assert scan.started_at is not None
    assert scan.finished_at is not None
    assert [item.value for item in results] == ["api.example.com"]


def test_task_scan_inexistente_retorna_missing(db):
    scan_id = str(uuid.uuid4())

    with patch("app.tasks.recon.SessionLocal", return_value=db):
        with patch.object(db, "close", return_value=None):
            result = run_subdomain_enum.__wrapped__(scan_id)

    assert result == {"scan_id": scan_id, "status": "missing"}


def test_task_erro_no_runner_marca_scan_como_failed(db):
    scan = _make_pending_scan(db)

    with patch("app.tasks.recon.run_subfinder", side_effect=RuntimeError("boom")):
        with patch("app.tasks.recon.SessionLocal", return_value=db):
            with patch.object(db, "close", return_value=None):
                with pytest.raises(RuntimeError, match="boom"):
                    run_subdomain_enum.__wrapped__(str(scan.id))

    db.refresh(scan)
    assert scan.status == ScanStatus.FAILED
    assert scan.error == "boom"
    assert scan.finished_at is not None
