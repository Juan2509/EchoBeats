"""Add per-instance PDF processing and page evidence."""

from alembic import op
import sqlalchemy as sa

from app.models.vector import Vector1536

revision = "0014_document_index"
down_revision = "0013_audio_index_queue"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document", sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempt", sa.Uuid()),
        sa.Column("error", sa.String(100)),
        sa.Column("model_key", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending','processing','ready','failed')", name=op.f("ck_document_status")),
    )
    op.create_table(
        "document_upload",
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("document.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("pdf", sa.LargeBinary(), nullable=False),
    )
    op.create_table(
        "document_chunk", sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("document.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(200)),
        sa.Column("extraction", sa.String(8), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector1536(), nullable=False),
        sa.UniqueConstraint("document_id", "page", "ordinal", name="uq_document_chunk_position"),
    )


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM document)")):
        raise RuntimeError("Hay documentos registrados. Conserva sus datos antes de revertir.")
    op.drop_table("document_chunk")
    op.drop_table("document_upload")
    op.drop_table("document")
