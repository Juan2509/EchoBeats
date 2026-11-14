"""Favoritos explícitos de la instalación local, sin historial de escucha."""
from alembic import op
import sqlalchemy as sa

revision = '0009_favorites'
down_revision = '0008_track_embeddings'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('favorite',
        sa.Column('track_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['track_id'], ['track.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('track_id'))


def downgrade():
    if op.get_bind().scalar(sa.text('SELECT EXISTS (SELECT 1 FROM favorite)')):
        raise RuntimeError('No se pueden retirar favoritos existentes. Conservar los datos antes de revertir.')
    op.drop_table('favorite')
