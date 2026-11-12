"""Conexión configurable; nunca registrar la URL con credenciales."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, URL, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError

from app.config import Settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_database_url(settings: Settings) -> URL | None:
    if settings.database_url.get_secret_value():
        try:
            url = make_url(settings.database_url.get_secret_value())
        except ArgumentError:
            raise ValueError("DATABASE_URL no válida.") from None
        if url.drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL debe usar postgresql+psycopg.")
        return url
    password = settings.postgres_password.get_secret_value()
    if not password:
        return None
    return URL.create(
        "postgresql+psycopg", username=settings.postgres_user, password=password,
        host=settings.postgres_host, port=settings.postgres_port, database=settings.postgres_db,
    )


def make_database_engine(settings: Settings) -> Engine | None:
    url = get_database_url(settings)
    if url is None:
        return None
    return create_engine(
        url, pool_pre_ping=True, pool_timeout=3, connect_args={"connect_timeout": 3},
        hide_parameters=True,
    )


def migration_config() -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    return config


def database_readiness(engine: Engine | None) -> dict[str, str]:
    checks = {"database": "unavailable", "pgvector": "unknown", "migrations": "unknown"}
    if engine is None:
        return checks
    try:
        with engine.connect() as connection:
            connection.execute(text("SET LOCAL statement_timeout = '3000ms'"))
            connection.execute(text("SELECT 1"))
            checks["database"] = "ok"
            extension = connection.scalar(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
            checks["pgvector"] = "ok" if extension else "missing"
            version_table = connection.scalar(text("SELECT to_regclass('public.alembic_version')"))
            current = set(connection.scalars(text("SELECT version_num FROM public.alembic_version"))) if version_table else set()
            expected = set(ScriptDirectory.from_config(migration_config()).get_heads())
            checks["migrations"] = "ok" if expected and current == expected else "pending"
    except SQLAlchemyError:
        # No devolver DSN, contraseña ni excepción del controlador al cliente.
        checks["database"] = "unavailable"
    return checks
