"""Ampliar referencias de audio conservando medios y catálogo existentes."""

from alembic import op
import sqlalchemy as sa

revision = '0004_audio_formats'
down_revision = '0003_metadata'
branch_labels = None
depends_on = None

OLD = r"storage_key ~ '^(audio|images)/[0-9a-f]{32}\.(mp3|png|jpg|jpeg|gif)$'"
NEW = r"storage_key ~ '^(audio|images)/[0-9a-f]{32}\.(mp3|wav|flac|ogg|opus|png|jpg|jpeg|gif)$'"


def upgrade():
    op.drop_constraint(op.f('ck_media_asset_key'), 'media_asset', type_='check')
    op.create_check_constraint(op.f('ck_media_asset_key'), 'media_asset', NEW)


def downgrade():
    # No borrar pistas ni sus archivos para poder retroceder de versión.
    if op.get_bind().scalar(sa.text(f'SELECT count(*) FROM media_asset WHERE NOT ({OLD})')):
        raise RuntimeError('No se puede retroceder: existen medios de formatos nuevos. Consérvalos y restaura en una base aislada.')
    op.drop_constraint(op.f('ck_media_asset_key'), 'media_asset', type_='check')
    op.create_check_constraint(op.f('ck_media_asset_key'), 'media_asset', OLD)
