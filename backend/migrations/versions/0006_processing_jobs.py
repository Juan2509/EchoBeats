"""Trabajos durables; no modifica audios ni metadatos del catálogo."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0006_processing_jobs'
down_revision = '0005_album_walls'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'processing_job',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('track_id', sa.Uuid(), sa.ForeignKey('track.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('operation', sa.String(32), nullable=False),
        sa.Column('input_version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_code', sa.String(40)), sa.Column('result', JSONB()),
        sa.Column('started_at', sa.DateTime(timezone=True)), sa.Column('finished_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('track_id', 'operation', 'input_version', name='uq_processing_job_track_id'),
        sa.CheckConstraint("operation = 'prepare_metadata'", name='ck_processing_job_operation'),
        sa.CheckConstraint("status IN ('pending','processing','completed','error','stale')", name='ck_processing_job_status'),
        sa.CheckConstraint('input_version > 0', name='ck_processing_job_version'),
        sa.CheckConstraint('attempts >= 0 AND attempts <= 3', name='ck_processing_job_attempts'),
    )
    op.create_index('ix_processing_job_pending', 'processing_job', ['created_at', 'id'], postgresql_where=sa.text("status = 'pending'"))


def downgrade():
    if op.get_bind().scalar(sa.text('SELECT EXISTS (SELECT 1 FROM processing_job)')):
        raise RuntimeError('Hay trabajos conservados. No se retira su historial mediante downgrade.')
    op.drop_index('ix_processing_job_pending', table_name='processing_job')
    op.drop_table('processing_job')
