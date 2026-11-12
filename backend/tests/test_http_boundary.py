"""Comprobar el arranque real y el límite local antes de añadir escrituras."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app


pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    settings = Settings(
        _env_file=None, allowed_hosts="localhost", allowed_origins="http://localhost:5173",
        database_url=SecretStr(""), postgres_password=SecretStr(""),
    )
    async with AsyncClient(transport=ASGITransport(app=create_app(settings)), base_url="http://localhost") as session:
        yield session


async def test_health_without_database_or_api_credentials(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_without_configuration_is_not_ready(client):
    response = await client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "unavailable"


async def test_unknown_api_does_not_return_fake_success(client):
    assert (await client.get("/api/v1/stations")).status_code == 404


async def test_untrusted_host_is_rejected(client):
    assert (await client.get("/api/v1/health", headers={"host": "untrusted.example"})).status_code == 400


async def test_browser_write_from_external_origin_is_rejected(client):
    response = await client.post("/api/v1/tracks", headers={"origin": "https://external.example"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "origin_not_allowed"


@pytest.mark.parametrize("headers", [{"origin": "http://localhost:5173"}, {}])
async def test_local_write_reaches_router_without_pretending_endpoint_exists(client, headers):
    assert (await client.post("/api/v1/stations", headers=headers)).status_code == 404
