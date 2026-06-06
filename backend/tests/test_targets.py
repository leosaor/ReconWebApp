from tests.factories import auth_headers, make_project, make_target, make_user


def test_criar_target_retorna_201(client, db):
    user = make_user(db, "target-create@recon.com")
    project = make_project(db, user)

    response = client.post(
        f"/api/v1/projects/{project.id}/targets",
        json={"value": "example.com", "kind": "domain"},
        headers=auth_headers(db, user),
    )

    assert response.status_code == 201
    assert response.json()["value"] == "example.com"


def test_target_duplicado_retorna_409(client, db):
    user = make_user(db, "target-duplicate@recon.com")
    project = make_project(db, user)
    make_target(db, project, value="example.com")

    response = client.post(
        f"/api/v1/projects/{project.id}/targets",
        json={"value": "example.com", "kind": "domain"},
        headers=auth_headers(db, user),
    )

    assert response.status_code == 409


def test_criar_target_em_projeto_alheio_retorna_404(client, db):
    owner = make_user(db, "target-owner@recon.com")
    other = make_user(db, "target-other@recon.com")
    project = make_project(db, owner)

    response = client.post(
        f"/api/v1/projects/{project.id}/targets",
        json={"value": "example.com", "kind": "domain"},
        headers=auth_headers(db, other),
    )

    assert response.status_code == 404


def test_listar_targets_retorna_lista_do_projeto(client, db):
    user = make_user(db, "target-list@recon.com")
    project = make_project(db, user)
    make_target(db, project, value="example.com")

    response = client.get(
        f"/api/v1/projects/{project.id}/targets",
        headers=auth_headers(db, user),
    )

    assert response.status_code == 200
    assert [target["value"] for target in response.json()] == ["example.com"]


def test_patch_target_atualiza_in_scope(client, db):
    user = make_user(db, "target-patch@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    response = client.patch(
        f"/api/v1/projects/{project.id}/targets/{target.id}",
        json={"in_scope": False},
        headers=auth_headers(db, user),
    )

    assert response.status_code == 200
    assert response.json()["in_scope"] is False


def test_delete_target_retorna_204(client, db):
    user = make_user(db, "target-delete@recon.com")
    project = make_project(db, user)
    target = make_target(db, project)

    response = client.delete(
        f"/api/v1/projects/{project.id}/targets/{target.id}",
        headers=auth_headers(db, user),
    )

    assert response.status_code == 204
