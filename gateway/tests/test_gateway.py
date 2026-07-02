"""Pruebas del API Gateway: autenticacion, seguridad, health y proxy."""
from app.security import create_access_token
from conftest import token_valido


def test_login_correcto(client):
    resp = client.post("/auth/login", json={"username": "director", "password": "campus123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "director"
    assert "access_token" in body


def test_login_incorrecto_da_401(client):
    resp = client.post("/auth/login", json={"username": "secretaria", "password": "mala"})
    assert resp.status_code == 401


def test_me_con_token(client):
    token = token_valido(client)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "secretaria"


def test_me_sin_token_da_401(client):
    assert client.get("/auth/me").status_code == 401


def test_token_invalido_da_401(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer token-falso"})
    assert resp.status_code == 401


def test_health_agregado(client):
    body = client.get("/health").json()
    assert body["gateway"] == "ok"
    assert body["overall"] == "ok"
    assert set(body["services"]) == {"academico", "pagos", "notificaciones", "asistencia", "analitica"}


def test_proxy_requiere_token(client):
    assert client.get("/api/academico/students").status_code == 401


def test_proxy_con_token(client):
    token = token_valido(client)
    resp = client.get("/api/academico/students", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_proxy_servicio_inexistente(client):
    token = token_valido(client)
    resp = client.get("/api/inexistente/x", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def _token(client, username):
    return client.post(
        "/auth/login", json={"username": username, "password": "campus123"}
    ).json()["access_token"]


def test_proxy_rol_sin_acceso_da_403(client):
    # secretaria (rol=academico) no puede acceder al servicio de pagos
    token = token_valido(client)
    resp = client.get("/api/pagos/payments", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_proxy_finanzas_accede_pagos(client):
    token = _token(client, "finanzas")
    resp = client.get("/api/pagos/payments", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_proxy_docente_accede_asistencia(client):
    token = _token(client, "docente")
    resp = client.get("/api/asistencia/students", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_proxy_director_accede_analitica(client):
    token = _token(client, "director")
    resp = client.get("/api/analitica/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_proxy_director_accede_notificaciones(client):
    token = _token(client, "director")
    resp = client.get("/api/notificaciones/notifications", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_proxy_finanzas_no_puede_acceder_academico(client):
    token = _token(client, "finanzas")
    assert client.get("/api/academico/students", headers={"Authorization": f"Bearer {token}"}).status_code == 403


def test_proxy_docente_no_puede_acceder_pagos(client):
    token = _token(client, "docente")
    assert client.get("/api/pagos/payments", headers={"Authorization": f"Bearer {token}"}).status_code == 403


def test_create_access_token_es_string():
    token = create_access_token("u", "rol", "Nombre")
    assert isinstance(token, str) and len(token) > 10


class _ClienteCaido:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url):
        raise __import__("httpx").HTTPError("servicio caido")

    async def request(self, *a, **k):
        raise __import__("httpx").HTTPError("servicio caido")


def test_health_con_servicio_caido(client, monkeypatch):
    import app.main as m
    monkeypatch.setattr(m.httpx, "AsyncClient", _ClienteCaido)
    body = client.get("/health").json()
    assert body["overall"] == "degraded"


def test_proxy_con_servicio_caido(client, monkeypatch):
    import app.main as m
    token = token_valido(client)
    monkeypatch.setattr(m.httpx, "AsyncClient", _ClienteCaido)
    resp = client.get("/api/academico/students", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 502


def test_token_expirado_da_401(client):
    import time

    from jose import jwt

    from shared.config import SecurityConfig

    expire = time.time() - 3600
    payload = {"sub": "secretaria", "role": "academico", "name": "Nombre", "exp": expire}
    token = jwt.encode(payload, SecurityConfig.JWT_SECRET, algorithm=SecurityConfig.JWT_ALGORITHM)

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token invalido o expirado"


def test_token_firma_invalida_da_401(client):
    from jose import jwt

    from shared.config import SecurityConfig

    payload = {"sub": "secretaria", "role": "academico", "name": "Nombre"}
    token = jwt.encode(payload, "clave_incorrecta_123", algorithm=SecurityConfig.JWT_ALGORITHM)

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token invalido o expirado"


def test_request_forwarding_headers(client, monkeypatch):
    from conftest import FakeResponse
    captured_headers = {}

    class FakeAsyncClientForHeaders:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def request(self, method, url, params=None, content=None, headers=None):
            nonlocal captured_headers
            captured_headers = headers
            return FakeResponse(200, {"proxied": True})

    import app.main as m
    monkeypatch.setattr(m.httpx, "AsyncClient", FakeAsyncClientForHeaders)

    token = token_valido(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Custom-Header": "mi-valor-personalizado",
        "Host": "localhost:8000",
        "Content-Length": "123"
    }
    resp = client.get(
        "/api/academico/students",
        headers=headers
    )
    assert resp.status_code == 200

    assert "host" not in captured_headers
    assert "content-length" not in captured_headers
    assert "authorization" not in captured_headers
    assert captured_headers.get("x-custom-header") == "mi-valor-personalizado"

