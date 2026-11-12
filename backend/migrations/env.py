from logging.config import fileConfig

from alembic import context
from sqlalchemy import MetaData, create_engine, pool

from app.config import Settings
from app.database import get_database_url

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# P05 conectará aquí los modelos del catálogo. No crear tablas al arrancar.
target_metadata = MetaData()


def run_migrations_offline():
    context.configure(
        dialect_name="postgresql", target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        configure_and_run(supplied_connection)
        return
    url = get_database_url(Settings())
    if url is None:
        raise RuntimeError("Configura POSTGRES_PASSWORD o DATABASE_URL antes de migrar.")
    engine = create_engine(url, poolclass=pool.NullPool, connect_args={"connect_timeout": 3}, hide_parameters=True)
    try:
        with engine.connect() as connection:
            configure_and_run(connection)
    finally:
        engine.dispose()


def configure_and_run(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
