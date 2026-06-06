import uuid
from unittest.mock import patch

import pytest

from app.models.scan import ScanStatus, ScanType
from app.models.scan_result import ScanResult
from app.tasks.recon import run_subdomain_enum
from tests.factories import make_project, make_scan, make_target, make_user


def test_task_sucesso_completa_scan(db):
    user = make_user(db, "task_ok@recon.com")
    project = make_project(db, user)
    target = make_target(db, project, "example.com")
    scan = make_scan(db, target, ScanType.SUBDOMAIN_ENUM, ScanStatus.PENDING)

    with patch("app.tasks.recon.SessionLocal", return_value=db), \
         patch.object(db, "close"), \
         patch("app.tasks.recon.run_subfinder", return_value=["sub1.example.com", "sub2.example.com"]):
        result = run_subdomain_enum(str(scan.id))

    db.refresh(scan)
    assert result["found"] == 2
    assert scan.status == ScanStatus.COMPLETED
    assert scan.started_at is not None
    assert scan.finished_at is not None

    results = db.query(ScanResult).filter_by(scan_id=scan.id).all()
    assert len(results) == 2
    values = {r.value for r in results}
    assert values == {"sub1.example.com", "sub2.example.com"}


def test_task_scan_inexistente_retorna_missing(db):
    fake_id = str(uuid.uuid4())

    with patch("app.tasks.recon.SessionLocal", return_value=db), \
         patch.object(db, "close"):
        result = run_subdomain_enum(fake_id)

    assert result["status"] == "missing"


def test_task_erro_no_runner_marca_failed(db):
    user = make_user(db, "task_fail@recon.com")
    project = make_project(db, user)
    target = make_target(db, project, "fail.com")
    scan = make_scan(db, target, ScanType.SUBDOMAIN_ENUM, ScanStatus.PENDING)

    with patch("app.tasks.recon.SessionLocal", return_value=db), \
         patch.object(db, "close"), \
         patch("app.tasks.recon.run_subfinder", side_effect=RuntimeError("subfinder crashed")), \
         pytest.raises(RuntimeError):
        run_subdomain_enum(str(scan.id))

    db.refresh(scan)
    assert scan.status == ScanStatus.FAILED
    assert "subfinder crashed" in scan.error
