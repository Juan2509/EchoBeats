"""Retirar canciones sin borrar originales ni historial."""
from alembic import op
import sqlalchemy as sa

revision = '0010_track_deletion'
down_revision = '0009_favorites'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('track', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    if op.get_bind().scalar(sa.text('SELECT EXISTS (SELECT 1 FROM track WHERE deleted_at IS NOT NULL)')):
        raise RuntimeError('Hay canciones retiradas. No revertir su estado ni perder el registro de eliminación.')
    op.drop_column('track', 'deleted_at')
