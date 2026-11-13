"""Fichas actuales e historial; no crea vectores ni modifica originales."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0007_track_descriptions'
down_revision = '0006_processing_jobs'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('track_description',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('track_id', sa.Uuid(), sa.ForeignKey('track.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(6000), nullable=False),
        sa.Column('features', JSONB(), nullable=False),
        sa.Column('source', sa.String(16), nullable=False),
        sa.Column('source_details', sa.String(2000), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('version > 0', name=op.f('ck_track_description_version')),
        sa.CheckConstraint("source IN ('manual','verified','metadata')", name=op.f('ck_track_description_source')),
    )
    op.create_table('description_revision',
        sa.Column('description_id', sa.Uuid(), sa.ForeignKey('track_description.id', ondelete='RESTRICT'), primary_key=True),
        sa.Column('version', sa.Integer(), primary_key=True),
        sa.Column('snapshot', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    if op.get_bind().scalar(sa.text('SELECT EXISTS (SELECT 1 FROM track_description)')):
        raise RuntimeError('Hay fichas musicales conservadas; no se elimina su historial mediante downgrade.')
    op.drop_table('description_revision')
    op.drop_table('track_description')
