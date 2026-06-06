from unittest.mock import patch

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


def test_criar_scan_com_target_fora_de_escopo_retorna_422(client, db):
    user = make_user(db, "scan-out-of-scope@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)
    target.in_scope = False
    db.commit()

    response = client.post(
        f"/api/v1/targets/{target.id}/scans",
        json={"scan_type": "subdomain_enum"},
        headers=auth_headers(db, user),
    )

    assert response.status_code == 422


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
