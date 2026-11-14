"""Embeddings pgvector y trabajos de indexación; conserva fichas y cola previa."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from app.models.vector import Vector1536

revision = '0008_track_embeddings'
down_revision = '0007_track_descriptions'
branch_labels = None
depends_on = None


def operation_constraint(expression):
    # 0006 podía aplicar la convención de nombres al nombre explícito: localizar
    # solo su CHECK de operation por definición, sin depender de ese detalle.
    for check in sa.inspect(op.get_bind()).get_check_constraints('processing_job'):
        if 'operation' in check['sqltext']:
            op.drop_constraint(op.f(check['name']), 'processing_job', type_='check')
    op.create_check_constraint(op.f('ck_processing_job_operation'), 'processing_job', expression)


def upgrade():
    op.add_column('processing_job', sa.Column('model_key', sa.String(200), nullable=False, server_default=''))
    op.add_column('processing_job', sa.Column('input_hash', sa.String(64)))
    op.drop_constraint('uq_processing_job_track_id', 'processing_job', type_='unique')
    op.create_unique_constraint('uq_processing_job_track_id', 'processing_job', ['track_id','operation','input_version','model_key'])
    operation_constraint("operation IN ('prepare_metadata','index_description')")
    op.create_table('track_embedding',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('description_id', sa.Uuid(), sa.ForeignKey('track_description.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('description_version', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('model_key', sa.String(200), nullable=False),
        sa.Column('input_format', sa.String(32), nullable=False),
        sa.Column('embedding', Vector1536(), nullable=False),
        sa.Column('usage', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('description_id','description_version','model_key', name='uq_track_embedding_description_id'),
        sa.CheckConstraint('description_version > 0', name=op.f('ck_track_embedding_version')),
    )


def downgrade():
    connection=op.get_bind()
    if connection.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM track_embedding) OR EXISTS (SELECT 1 FROM processing_job WHERE operation = 'index_description')")):
        raise RuntimeError('Hay vectores o trabajos de indexación conservados; no se elimina su historial.')
    op.drop_table('track_embedding')
    operation_constraint("operation = 'prepare_metadata'")
    op.drop_constraint('uq_processing_job_track_id','processing_job',type_='unique')
    op.create_unique_constraint('uq_processing_job_track_id','processing_job',['track_id','operation','input_version'])
    op.drop_column('processing_job','input_hash')
    op.drop_column('processing_job','model_key')
