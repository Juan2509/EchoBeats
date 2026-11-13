"""Muros independientes y elementos; conservar todos los álbumes y recursos."""
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision = '0005_album_walls'
down_revision = '0004_audio_formats'
branch_labels = None
depends_on = None


def upgrade():
    walls = op.create_table(
        'wall',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('album_id', sa.Uuid(), nullable=False),
        sa.Column('schema_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('revision', sa.Integer(), server_default='1', nullable=False),
        sa.Column('background_color', sa.String(7), server_default='#242038', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_wall')),
        sa.ForeignKeyConstraint(['album_id'], ['album.id'], ondelete='RESTRICT', name=op.f('fk_wall_album_id_album')),
        sa.UniqueConstraint('album_id', name=op.f('uq_wall_album_id')),
        sa.CheckConstraint('schema_version = 1', name=op.f('ck_wall_schema_version')),
        sa.CheckConstraint('revision > 0', name=op.f('ck_wall_revision')),
        sa.CheckConstraint("background_color ~ '^#[0-9A-Fa-f]{6}$'", name=op.f('ck_wall_background_color')),
    )
    op.create_table(
        'wall_element',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('wall_id', sa.Uuid(), nullable=False),
        sa.Column('asset_id', sa.Uuid(), nullable=False),
        sa.Column('kind', sa.String(16), nullable=False),
        sa.Column('cx', sa.Double(), nullable=False), sa.Column('cy', sa.Double(), nullable=False),
        sa.Column('width', sa.Double(), nullable=False), sa.Column('height', sa.Double(), nullable=False),
        sa.Column('rotation_deg', sa.Double(), nullable=False), sa.Column('z_index', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_wall_element')),
        sa.ForeignKeyConstraint(['wall_id'], ['wall.id'], ondelete='RESTRICT', name=op.f('fk_wall_element_wall_id_wall')),
        sa.ForeignKeyConstraint(['asset_id'], ['media_asset.id'], ondelete='RESTRICT', name=op.f('fk_wall_element_asset_id_media_asset')),
        sa.CheckConstraint("kind IN ('poster','sticker','image','gif')", name=op.f('ck_wall_element_kind')),
        sa.CheckConstraint('cx >= 0 AND cx <= 1 AND cy >= 0 AND cy <= 1', name=op.f('ck_wall_element_center')),
        sa.CheckConstraint('width >= 0.03 AND width <= 0.60 AND height >= 0.03 AND height <= 0.60', name=op.f('ck_wall_element_size')),
        sa.CheckConstraint('rotation_deg >= -180 AND rotation_deg < 180', name=op.f('ck_wall_element_rotation')),
        sa.CheckConstraint('z_index >= 0 AND z_index <= 29', name=op.f('ck_wall_element_z_index')),
    )
    op.create_index(op.f('ix_wall_element_wall_id'), 'wall_element', ['wall_id'])
    connection = op.get_bind()
    ids = connection.scalars(sa.text('SELECT id FROM album')).all()
    if ids:
        connection.execute(walls.insert(), [{'id': uuid4(), 'album_id': identity} for identity in ids])


def downgrade():
    connection = op.get_bind()
    customized = connection.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM wall WHERE revision > 1 OR background_color <> '#242038') OR EXISTS (SELECT 1 FROM wall_element)"))
    if customized:
        raise RuntimeError('No se puede retirar P12: hay muros guardados. Conserva el esquema y respalda los datos.')
    op.drop_table('wall_element')
    op.drop_table('wall')
