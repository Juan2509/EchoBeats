import os
from uuid import uuid4

from alembic import command
import pytest
from sqlalchemy import create_engine, text

from app.config import Settings
from app.database import get_database_url, migration_config


@pytest.fixture(autouse=True)
def isolated_runtime_settings(tmp_path, monkeypatch):
    # Settings() creado de nuevo en un helper también debe heredar medios temporales.
    # _env_file=None no desactiva variables heredadas del contenedor.
    monkeypatch.setenv('MEDIA_ROOT', str(tmp_path / 'media'))
    monkeypatch.setenv('AI_ENABLED', 'false')
    monkeypatch.setenv('OPENAI_API_KEY', '')
    monkeypatch.setenv('PROCESSING_WORKER_ENABLED', 'false')


@pytest.fixture
def catalog_engine():
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Activar RUN_DB_TESTS=1 para pruebas con PostgreSQL real.")
    url = get_database_url(Settings())
    assert url is not None
    name = f"echobeats_test_{uuid4().hex}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT", hide_parameters=True)
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(url.set(database=name), hide_parameters=True)
    try:
        with engine.begin() as connection:
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()


@pytest.fixture
def anyio_backend():
    return "asyncio"
