import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.services.auth_service import ensure_bootstrap_admin


def _register(client: TestClient, email: str, password: str = "senha1234") -> dict:
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def _create_user(
    db: Session,
    email: str,
    password: str = "senha1234",
    role: UserRole = UserRole.PENTESTER,
    is_active: bool = True,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client: TestClient, email: str, password: str = "senha1234") -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_registro_publico_cria_usuario_viewer_inativo(client, db):
    _register(client, "novo@recon.com")

    user = db.query(User).filter(User.email == "novo@recon.com").one()
    assert user.role == UserRole.VIEWER
    assert user.is_active is False


def test_email_duplicado_retorna_mensagem_generica(client, db):
    _register(client, "dup@recon.com")
    response = client.post("/auth/register", json={"email": "dup@recon.com", "password": "senha1234"})

    assert response.status_code == 201
    assert "message" in response.json()
    assert db.query(User).filter(User.email == "dup@recon.com").count() == 1


def test_senha_curta_retorna_422(client):
    response = client.post("/auth/register", json={"email": "x@recon.com", "password": "abc"})
    assert response.status_code == 422


def test_bootstrap_admin_cria_admin_ativo(db):
    original_email = settings.bootstrap_admin_email
    original_password = settings.bootstrap_admin_password
    original_full_name = settings.bootstrap_admin_full_name
    try:
        settings.bootstrap_admin_email = "bootstrap@recon.com"
        settings.bootstrap_admin_password = "BootstrapPass123!"
        settings.bootstrap_admin_full_name = "Bootstrap Admin"

        ensure_bootstrap_admin(db)

        user = db.query(User).filter(User.email == "bootstrap@recon.com").one()
        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.full_name == "Bootstrap Admin"
    finally:
        settings.bootstrap_admin_email = original_email
        settings.bootstrap_admin_password = original_password
        settings.bootstrap_admin_full_name = original_full_name


def test_login_retorna_access_token(client, db):
    _create_user(db, "login@recon.com")
    response = client.post("/auth/login", json={"email": "login@recon.com", "password": "senha1234"})

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.cookies.get("refresh_token") is not None


def test_login_aceita_username_sem_dominio(client, db):
    _create_user(db, "usuario@recon.com")
    response = client.post("/auth/login", json={"username": "usuario", "password": "senha1234"})

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_senha_errada_retorna_401(client, db):
    _create_user(db, "wrong@recon.com")
    response = client.post("/auth/login", json={"email": "wrong@recon.com", "password": "errada"})

    assert response.status_code == 401


def test_login_email_inexistente_retorna_401(client):
    response = client.post("/auth/login", json={"email": "nao@existe.com", "password": "senha1234"})
    assert response.status_code == 401


def test_login_usuario_inativo_retorna_403(client, db):
    _create_user(db, "inactive@recon.com", is_active=False)
    response = client.post("/auth/login", json={"email": "inactive@recon.com", "password": "senha1234"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Usuario inativo, contate um administrador"


def test_me_com_jwt_retorna_usuario(client, db):
    _create_user(db, "me@recon.com")
    token = _login(client, "me@recon.com")
    response = client.get("/auth/me", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["email"] == "me@recon.com"


def test_me_sem_token_retorna_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_refresh_retorna_novo_access_token(client, db):
    _create_user(db, "refresh@recon.com")
    client.post("/auth/login", json={"email": "refresh@recon.com", "password": "senha1234"})
    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_criar_api_key_retorna_raw_key(client, db):
    _create_user(db, "apikey@recon.com")
    token = _login(client, "apikey@recon.com")
    response = client.post("/auth/api-keys", json={"name": "CLI"}, headers=_auth(token))

    assert response.status_code == 201
    data = response.json()
    assert data["raw_key"].startswith("rwa_")
    assert "raw_key" not in client.get("/auth/api-keys", headers=_auth(token)).json()[0]


def test_autenticar_com_api_key(client, db):
    _create_user(db, "apikeyauth@recon.com")
    token = _login(client, "apikeyauth@recon.com")
    raw_key = client.post("/auth/api-keys", json={"name": "CLI"}, headers=_auth(token)).json()["raw_key"]
    response = client.get("/auth/me", headers={"X-API-Key": raw_key})

    assert response.status_code == 200
    assert response.json()["email"] == "apikeyauth@recon.com"


def test_revogar_api_key(client, db):
    _create_user(db, "revoke@recon.com")
    token = _login(client, "revoke@recon.com")
    payload = client.post("/auth/api-keys", json={"name": "tmp"}, headers=_auth(token)).json()
    raw_key, key_id = payload["raw_key"], payload["id"]

    client.delete(f"/auth/api-keys/{key_id}", headers=_auth(token))
    response = client.get("/auth/me", headers={"X-API-Key": raw_key})

    assert response.status_code == 401


def test_admin_lista_todos_usuarios(client, db):
    _create_user(db, "adm2@recon.com", role=UserRole.ADMIN)
    _create_user(db, "usr2@recon.com")
    token = _login(client, "adm2@recon.com")
    response = client.get("/users", headers=_auth(token))

    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_pentester_nao_acessa_lista_usuarios(client, db):
    _create_user(db, "adm3@recon.com", role=UserRole.ADMIN)
    user = _create_user(db, "pen3@recon.com", is_active=False)
    admin_token = _login(client, "adm3@recon.com")
    client.patch(
        f"/users/{user.id}",
        json={"role": "pentester", "is_active": True},
        headers=_auth(admin_token),
    )

    token = _login(client, "pen3@recon.com")
    response = client.get("/users", headers=_auth(token))

    assert response.status_code == 403
