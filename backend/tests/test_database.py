"""Migraciones y recuperación de readiness sobre PostgreSQL real y aislado."""

import os
from uuid import uuid4

from alembic import command
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import create_engine, text

from app.config import Settings
from app.database import database_readiness, get_database_url, migration_config
from app.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def database_engine():
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Activar RUN_DB_TESTS=1 para pruebas con PostgreSQL real.")
    url = get_database_url(Settings())
    assert url is not None, "Falta conexión de prueba"
    name = f"echobeats_test_{uuid4().hex}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT", hide_parameters=True)
    # Nombre exclusivamente generado aquí, nunca interpolado desde una entrada.
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(url.set(database=name), hide_parameters=True)
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()


def migrate(engine, operation, target):
    with engine.begin() as connection:
        config = migration_config()
        config.attributes["connection"] = connection
        operation(config, target)


def test_migration_roundtrip_and_real_vector_distance(database_engine):
    engine = database_engine
    checks = database_readiness(engine)
    assert checks == {"database": "ok", "pgvector": "missing", "migrations": "pending"}
    migrate(engine, command.upgrade, "head")
    assert all(value == "ok" for value in database_readiness(engine).values())
    # Repetir upgrade no duplica ni destruye datos.
    migrate(engine, command.upgrade, "head")
    with engine.begin() as connection:
        connection.execute(text("CREATE TEMP TABLE vector_probe (id int, embedding vector(3)) ON COMMIT DROP"))
        connection.execute(text("INSERT INTO vector_probe VALUES (1, '[1,0,0]'), (2, '[0,1,0]')"))
        result = connection.execute(text("SELECT id, embedding <=> '[1,0,0]'::vector AS distance FROM vector_probe ORDER BY distance")).all()
        assert result[0].id == 1
        assert result[0].distance == pytest.approx(0)
        assert result[1].distance == pytest.approx(1)
    migrate(engine, command.downgrade, "base")
    assert database_readiness(engine)["pgvector"] == "missing"
    migrate(engine, command.upgrade, "head")
    assert all(value == "ok" for value in database_readiness(engine).values())


@pytest.mark.anyio
async def test_readiness_reports_pending_migrations_and_recovers(database_engine):
    # Base compartida solo entre estas pruebas, nunca la base principal.
    engine = database_engine
    app = create_app(Settings())
    original_engine = app.state.database_engine
    app.state.database_engine = engine
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
            migrate(engine, command.downgrade, "base")
            response = await client.get("/api/v1/ready")
            assert response.status_code == 503
            assert response.json()["checks"]["migrations"] == "pending"
            assert (await client.get("/api/v1/health")).status_code == 200
            migrate(engine, command.upgrade, "head")
            assert (await client.get("/api/v1/ready")).status_code == 200
    finally:
        if original_engine is not None:
            original_engine.dispose()


@pytest.fixture
def anyio_backend():
    return "asyncio"
