"""Store audio embeddings independently of description embeddings."""

from alembic import op
import sqlalchemy as sa

from app.models.vector import AudioVector26


revision = "0012_audio_embeddings"
down_revision = "0011_wall_full_size"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "track_audio_embedding",
        sa.Column("track_id", sa.Uuid(), sa.ForeignKey("track.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("model_key", sa.String(80), primary_key=True),
        sa.Column("audio_asset_id", sa.Uuid(), sa.ForeignKey("media_asset.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("embedding", AudioVector26(), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM track_audio_embedding)")):
        raise RuntimeError("El índice acústico contiene vectores guardados.")
    op.drop_table("track_audio_embedding")
