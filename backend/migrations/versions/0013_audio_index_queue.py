"""Persist acoustic indexing attempts across worker restarts."""

from alembic import op
import sqlalchemy as sa


revision = "0013_audio_index_queue"
down_revision = "0012_audio_embeddings"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audio_index_attempt",
        sa.Column("track_id", sa.Uuid(), sa.ForeignKey("track.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("model_key", sa.String(80), primary_key=True),
        sa.Column("content_sha256", sa.String(64), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error", sa.String(200)),
        sa.CheckConstraint(
            "(status = 'processing' AND error IS NULL) OR (status = 'failed' AND error IS NOT NULL)",
            name=op.f("ck_audio_index_attempt_status"),
        ),
    )


def downgrade():
    op.drop_table("audio_index_attempt")
