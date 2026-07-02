"""Configuracion de pruebas del API Gateway (httpx simulado)."""
import app.main as main_module
import pytest
from fastapi.testclient import TestClient


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data if data is not None else {"ok": True}
        self.headers = {"content-type": "application/json"}

    def json(self):
        return self._data

    @property
    def text(self):
        return "texto"


class FakeAsyncClient:
    """Sustituye httpx.AsyncClient para no contactar servicios reales."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url):
        return FakeResponse(200, {"status": "ok"})

    async def request(self, method, url, params=None, content=None, headers=None):
        return FakeResponse(200, {"proxied": True, "url": url})


@pytest.fixture(autouse=True)
def _no_httpx(monkeypatch):
    monkeypatch.setattr(main_module.httpx, "AsyncClient", FakeAsyncClient)
    yield


@pytest.fixture
def client():
    return TestClient(main_module.app)


def token_valido(client):
    resp = client.post("/auth/login", json={"username": "secretaria", "password": "campus123"})
    return resp.json()["access_token"]
