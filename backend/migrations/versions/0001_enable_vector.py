"""Activar pgvector sin crear todavía tablas musicales ni embeddings."""

from alembic import op

revision = "0001_enable_vector"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade():
    # Sin CASCADE: no eliminar columnas/tablas dependientes silenciosamente.
    op.execute("DROP EXTENSION IF EXISTS vector")
