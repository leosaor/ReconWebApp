from unittest.mock import patch

from app.models.audit_log import AuditLog
from app.models.scan import ScanStatus, ScanType
from app.models.scan_result import ScanResult
from app.models.user import UserRole
from tests.factories import auth_headers, make_project, make_scan, make_target, make_user


def test_criar_scan_retorna_202_pending_e_enfileira_task(client, db):
    user = make_user(db, "scan-create@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    with patch("app.tasks.recon.run_subdomain_enum.delay") as delay:
        response = client.post(
            f"/api/v1/targets/{target.id}/scans",
            json={"scan_type": "subdomain_enum"},
            headers=auth_headers(db, user),
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ScanStatus.PENDING
    assert data["scan_type"] == ScanType.SUBDOMAIN_ENUM
    delay.assert_called_once_with(data["id"])

    audit = db.query(AuditLog).filter(AuditLog.action == "scan.enqueue").one()
    assert audit.user_id == user.id
    assert audit.entity == "scan"
    assert audit.entity_id == data["id"]
    assert audit.metadata_["scan_type"] == ScanType.SUBDOMAIN_ENUM
    assert audit.metadata_["target"] == target.value
    assert audit.metadata_["project_id"] == str(project.id)


def test_criar_http_probe_retorna_202_pending_e_enfileira_task(client, db):
    user = make_user(db, "scan-http@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    with patch("app.tasks.recon.run_http_probe.delay") as delay:
        response = client.post(
            f"/api/v1/targets/{target.id}/scans",
            json={"scan_type": "http_probe"},
            headers=auth_headers(db, user),
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ScanStatus.PENDING
    assert data["scan_type"] == ScanType.HTTP_PROBE
    delay.assert_called_once_with(data["id"])


def test_criar_port_scan_retorna_202_pending_e_enfileira_task(client, db):
    user = make_user(db, "scan-port@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    with patch("app.tasks.recon.run_port_scan.delay") as delay:
        response = client.post(
            f"/api/v1/targets/{target.id}/scans",
            json={"scan_type": "port_scan"},
            headers=auth_headers(db, user),
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ScanStatus.PENDING
    assert data["scan_type"] == ScanType.PORT_SCAN
    delay.assert_called_once_with(data["id"])


def test_criar_tls_scan_retorna_202_pending_e_enfileira_task(client, db):
    user = make_user(db, "scan-tls@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    with patch("app.tasks.recon.run_tls_scan.delay") as delay:
        response = client.post(
            f"/api/v1/targets/{target.id}/scans",
            json={"scan_type": "tls_scan"},
            headers=auth_headers(db, user),
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ScanStatus.PENDING
    assert data["scan_type"] == ScanType.TLS_SCAN
    delay.assert_called_once_with(data["id"])


def test_criar_content_fuzz_retorna_202_pending_e_enfileira_task(client, db):
    user = make_user(db, "scan-fuzz@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    with patch("app.tasks.recon.run_content_fuzz.delay") as delay:
        response = client.post(
            f"/api/v1/targets/{target.id}/scans",
            json={"scan_type": "content_fuzz"},
            headers=auth_headers(db, user),
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ScanStatus.PENDING
    assert data["scan_type"] == ScanType.CONTENT_FUZZ
    delay.assert_called_once_with(data["id"])


def test_criar_git_dump_retorna_202_pending_e_enfileira_task(client, db):
    user = make_user(db, "scan-git-dump@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    with patch("app.tasks.recon.run_git_dump.delay") as delay:
        response = client.post(
            f"/api/v1/targets/{target.id}/scans",
            json={"scan_type": "git_dump"},
            headers=auth_headers(db, user),
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ScanStatus.PENDING
    assert data["scan_type"] == ScanType.GIT_DUMP
    delay.assert_called_once_with(data["id"])


def test_criar_nuclei_scan_retorna_202_pending_e_enfileira_task(client, db):
    user = make_user(db, "scan-nuclei@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    with patch("app.tasks.recon.run_nuclei_scan.delay") as delay:
        response = client.post(
            f"/api/v1/targets/{target.id}/scans",
            json={"scan_type": "nuclei_scan"},
            headers=auth_headers(db, user),
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ScanStatus.PENDING
    assert data["scan_type"] == ScanType.NUCLEI_SCAN
    delay.assert_called_once_with(data["id"])


def test_viewer_nao_cria_scan(client, db):
    viewer = make_user(db, "scan-viewer@recon.com", role=UserRole.VIEWER)
    project = make_project(db, viewer)
    target = make_target(db, project)

    response = client.post(
        f"/api/v1/targets/{target.id}/scans",
        json={"scan_type": "subdomain_enum"},
        headers=auth_headers(db, viewer),
    )

    assert response.status_code == 403


def test_criar_scan_em_target_alheio_retorna_404(client, db):
    owner = make_user(db, "scan-owner@recon.com")
    other = make_user(db, "scan-other@recon.com")
    project = make_project(db, owner)
    target = make_target(db, project)

    response = client.post(
        f"/api/v1/targets/{target.id}/scans",
        json={"scan_type": "subdomain_enum"},
        headers=auth_headers(db, other),
    )

    assert response.status_code == 404


def test_get_scan_retorna_status(client, db):
    user = make_user(db, "scan-get@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)
    scan = make_scan(db, target, status=ScanStatus.COMPLETED)

    response = client.get(
        f"/api/v1/scans/{scan.id}",
        headers=auth_headers(db, user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == ScanStatus.COMPLETED


def test_get_scan_results_retorna_resultados(client, db):
    user = make_user(db, "scan-results@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)
    scan = make_scan(db, target)
    db.add(ScanResult(scan_id=scan.id, value="api.example.com", data={"source": "test"}))
    db.commit()

    response = client.get(
        f"/api/v1/scans/{scan.id}/results",
        headers=auth_headers(db, user),
    )

    assert response.status_code == 200
    assert response.json()[0]["value"] == "api.example.com"
    assert response.json()[0]["data"] == {"source": "test"}
