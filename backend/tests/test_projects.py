from app.models.user import UserRole
from tests.factories import auth_headers, make_project, make_user


def test_criar_projeto_com_pentester_retorna_201(client, db):
    user = make_user(db, "pentester-project@recon.com")

    response = client.post(
        "/api/v1/projects",
        json={"name": "External Recon", "description": "Client scope"},
        headers=auth_headers(db, user),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "External Recon"
    assert data["owner_id"] == str(user.id)


def test_pentester_lista_apenas_seus_projetos(client, db):
    owner = make_user(db, "owner-projects@recon.com")
    other = make_user(db, "other-projects@recon.com")
    own_project = make_project(db, owner, name="Own")
    make_project(db, other, name="Other")

    response = client.get("/api/v1/projects", headers=auth_headers(db, owner))

    assert response.status_code == 200
    assert [project["id"] for project in response.json()] == [str(own_project.id)]


def test_admin_lista_todos_os_projetos(client, db):
    admin = make_user(db, "admin-projects@recon.com", role=UserRole.ADMIN)
    first_owner = make_user(db, "first-owner@recon.com")
    second_owner = make_user(db, "second-owner@recon.com")
    make_project(db, first_owner, name="First")
    make_project(db, second_owner, name="Second")

    response = client.get("/api/v1/projects", headers=auth_headers(db, admin))

    assert response.status_code == 200
    assert {project["name"] for project in response.json()} == {"First", "Second"}


def test_viewer_nao_cria_projeto(client, db):
    viewer = make_user(db, "viewer-project@recon.com", role=UserRole.VIEWER)

    response = client.post(
        "/api/v1/projects",
        json={"name": "Blocked"},
        headers=auth_headers(db, viewer),
    )

    assert response.status_code == 403


def test_criar_target_interno_retorna_400(client, db):
    user = make_user(db, "internal-target@recon.com")
    project = make_project(db, user)

    response = client.post(
        f"/api/v1/projects/{project.id}/targets",
        json={"value": "10.0.0.1"},
        headers=auth_headers(db, user),
    )

    assert response.status_code == 400
    assert "interno" in response.json()["detail"]


def test_get_projeto_de_outro_usuario_retorna_404(client, db):
    owner = make_user(db, "project-owner@recon.com")
    other = make_user(db, "project-other@recon.com")
    project = make_project(db, owner)

    response = client.get(
        f"/api/v1/projects/{project.id}",
        headers=auth_headers(db, other),
    )

    assert response.status_code == 404


def test_patch_projeto_atualiza_nome(client, db):
    user = make_user(db, "patch-project@recon.com")
    project = make_project(db, user, name="Before")

    response = client.patch(
        f"/api/v1/projects/{project.id}",
        json={"name": "After"},
        headers=auth_headers(db, user),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "After"


def test_delete_projeto_retorna_204(client, db):
    user = make_user(db, "delete-project@recon.com")
    project = make_project(db, user)

    response = client.delete(
        f"/api/v1/projects/{project.id}",
        headers=auth_headers(db, user),
    )

    assert response.status_code == 204
