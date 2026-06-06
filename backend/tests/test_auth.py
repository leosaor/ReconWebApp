import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def _register(client: TestClient, email: str, password: str = "senha1234") -> dict:
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()


def _login(client: TestClient, email: str, password: str = "senha1234") -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── registro ─────────────────────────────────────────────────────────────────

def test_primeiro_usuario_vira_admin(client):
    user = _register(client, "admin@recon.com")
    assert user["role"] == "admin"
    assert user["is_active"] is True


def test_segundo_usuario_vira_pentester(client):
    _register(client, "admin@recon.com")
    user = _register(client, "pentester@recon.com")
    assert user["role"] == "pentester"


def test_email_duplicado_retorna_409(client):
    _register(client, "dup@recon.com")
    r = client.post("/auth/register", json={"email": "dup@recon.com", "password": "senha1234"})
    assert r.status_code == 409


def test_senha_curta_retorna_422(client):
    r = client.post("/auth/register", json={"email": "x@recon.com", "password": "abc"})
    assert r.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────────

def test_login_retorna_access_token(client):
    _register(client, "login@recon.com")
    r = client.post("/auth/login", json={"email": "login@recon.com", "password": "senha1234"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.cookies.get("refresh_token") is not None


def test_login_aceita_username_sem_dominio(client):
    _register(client, "usuario@recon.com")
    r = client.post("/auth/login", json={"username": "usuario", "password": "senha1234"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_senha_errada_retorna_401(client):
    _register(client, "wrong@recon.com")
    r = client.post("/auth/login", json={"email": "wrong@recon.com", "password": "errada"})
    assert r.status_code == 401


def test_login_email_inexistente_retorna_401(client):
    r = client.post("/auth/login", json={"email": "nao@existe.com", "password": "senha1234"})
    assert r.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────

def test_me_com_jwt_retorna_usuario(client):
    _register(client, "me@recon.com")
    token = _login(client, "me@recon.com")
    r = client.get("/auth/me", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["email"] == "me@recon.com"


def test_me_sem_token_retorna_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


# ── refresh token ─────────────────────────────────────────────────────────────

def test_refresh_retorna_novo_access_token(client):
    _register(client, "refresh@recon.com")
    client.post("/auth/login", json={"email": "refresh@recon.com", "password": "senha1234"})
    r = client.post("/auth/refresh")
    assert r.status_code == 200
    assert "access_token" in r.json()


# ── API keys ──────────────────────────────────────────────────────────────────

def test_criar_api_key_retorna_raw_key(client):
    _register(client, "apikey@recon.com")
    token = _login(client, "apikey@recon.com")
    r = client.post("/auth/api-keys", json={"name": "CLI"}, headers=_auth(token))
    assert r.status_code == 201
    data = r.json()
    assert data["raw_key"].startswith("rwa_")
    assert "raw_key" not in client.get("/auth/api-keys", headers=_auth(token)).json()[0]


def test_autenticar_com_api_key(client):
    _register(client, "apikeyauth@recon.com")
    token = _login(client, "apikeyauth@recon.com")
    raw_key = client.post("/auth/api-keys", json={"name": "CLI"}, headers=_auth(token)).json()["raw_key"]
    r = client.get("/auth/me", headers={"X-API-Key": raw_key})
    assert r.status_code == 200
    assert r.json()["email"] == "apikeyauth@recon.com"


def test_revogar_api_key(client):
    _register(client, "revoke@recon.com")
    token = _login(client, "revoke@recon.com")
    resp = client.post("/auth/api-keys", json={"name": "tmp"}, headers=_auth(token)).json()
    raw_key, key_id = resp["raw_key"], resp["id"]
    client.delete(f"/auth/api-keys/{key_id}", headers=_auth(token))
    r = client.get("/auth/me", headers={"X-API-Key": raw_key})
    assert r.status_code == 401


# ── RBAC / admin ──────────────────────────────────────────────────────────────

def test_admin_lista_todos_usuarios(client):
    _register(client, "adm2@recon.com")
    _register(client, "usr2@recon.com")
    token = _login(client, "adm2@recon.com")
    r = client.get("/users", headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_pentester_nao_acessa_lista_usuarios(client):
    _register(client, "adm3@recon.com")
    _register(client, "pen3@recon.com")
    token = _login(client, "pen3@recon.com")
    r = client.get("/users", headers=_auth(token))
    assert r.status_code == 403
