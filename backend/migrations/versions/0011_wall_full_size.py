"""Permitir objetos del tamaño completo del muro sin modificar diseños."""
from alembic import op
import sqlalchemy as sa
revision='0011_wall_full_size'
down_revision='0010_track_deletion'
branch_labels=None
depends_on=None

def upgrade():
    op.drop_constraint(op.f('ck_wall_element_size'),'wall_element',type_='check')
    op.create_check_constraint(op.f('ck_wall_element_size'),'wall_element','width >= 0.03 AND width <= 1.0 AND height >= 0.03 AND height <= 1.0')

def downgrade():
    if op.get_bind().scalar(sa.text('SELECT EXISTS (SELECT 1 FROM wall_element WHERE width > 0.60 OR height > 0.60)')):
        raise RuntimeError('Hay objetos que superan el límite anterior. No recortar ni borrar diseños al revertir.')
    op.drop_constraint(op.f('ck_wall_element_size'),'wall_element',type_='check')
    op.create_check_constraint(op.f('ck_wall_element_size'),'wall_element','width >= 0.03 AND width <= 0.60 AND height >= 0.03 AND height <= 0.60')
