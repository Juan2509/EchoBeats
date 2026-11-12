"""Create catalog and managed assets

Revision ID: 0002_catalog
Revises: 0001_enable_vector
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002_catalog'
down_revision = '0001_enable_vector'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('artist',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('normalized_name', sa.String(length=320), nullable=False),
    sa.CheckConstraint('length(trim(name)) > 0', name=op.f('ck_artist_name')),
    sa.CheckConstraint('length(trim(normalized_name)) > 0', name=op.f('ck_artist_normalized_name')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_artist')),
    sa.UniqueConstraint('normalized_name', name=op.f('uq_artist_normalized_name'))
    )
    op.create_table('media_asset',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('storage_key', sa.String(length=255), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('original_name', sa.String(length=255), nullable=False),
    sa.Column('mime_type', sa.String(length=80), nullable=False),
    sa.Column('byte_size', sa.BigInteger(), nullable=False),
    sa.Column('width_px', sa.Integer(), nullable=True),
    sa.Column('height_px', sa.Integer(), nullable=True),
    sa.Column('frame_count', sa.Integer(), nullable=True),
    sa.Column('static_preview_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('audio','image','gif','cover')", name=op.f('ck_media_asset_kind')),
    sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name=op.f('ck_media_asset_hash')),
    sa.CheckConstraint("storage_key ~ '^(audio|images)/[0-9a-f]{32}\\.(mp3|png|jpg|jpeg|gif)$'", name=op.f('ck_media_asset_key')),
    sa.CheckConstraint('byte_size > 0', name=op.f('ck_media_asset_size')),
    sa.CheckConstraint('frame_count IS NULL OR frame_count > 0', name=op.f('ck_media_asset_frames')),
    sa.CheckConstraint('height_px IS NULL OR height_px > 0', name=op.f('ck_media_asset_height')),
    sa.CheckConstraint('static_preview_id IS NULL OR static_preview_id <> id', name=op.f('ck_media_asset_preview')),
    sa.CheckConstraint('width_px IS NULL OR width_px > 0', name=op.f('ck_media_asset_width')),
    sa.ForeignKeyConstraint(['static_preview_id'], ['media_asset.id'], name=op.f('fk_media_asset_static_preview_id_media_asset'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_media_asset')),
    sa.UniqueConstraint('storage_key', name=op.f('uq_media_asset_storage_key'))
    )
    op.create_index(op.f('ix_media_asset_sha256'), 'media_asset', ['sha256'], unique=False)
    op.create_table('album',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('cover_asset_id', sa.Uuid(), nullable=True),
    sa.Column('system_key', sa.String(length=32), nullable=True),
    sa.Column('revision', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("system_key IS NULL OR (system_key = 'unknown' AND title = 'Sin álbum')", name=op.f('ck_album_system_album')),
    sa.CheckConstraint('length(trim(title)) > 0', name=op.f('ck_album_title')),
    sa.CheckConstraint('revision > 0', name=op.f('ck_album_revision')),
    sa.ForeignKeyConstraint(['cover_asset_id'], ['media_asset.id'], name=op.f('fk_album_cover_asset_id_media_asset'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_album')),
    sa.UniqueConstraint('system_key', name=op.f('uq_album_system_key'))
    )
    op.create_table('playlist',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('appearance', sa.String(length=16), server_default='vinyl', nullable=False),
    sa.Column('image_asset_id', sa.Uuid(), nullable=True),
    sa.Column('revision', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("appearance IN ('vinyl','image')", name=op.f('ck_playlist_appearance')),
    sa.CheckConstraint('length(trim(name)) > 0', name=op.f('ck_playlist_name')),
    sa.CheckConstraint('revision > 0', name=op.f('ck_playlist_revision')),
    sa.ForeignKeyConstraint(['image_asset_id'], ['media_asset.id'], name=op.f('fk_playlist_image_asset_id_media_asset'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_playlist'))
    )
    op.create_table('album_artist',
    sa.Column('album_id', sa.Uuid(), nullable=False),
    sa.Column('artist_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('position >= 0', name=op.f('ck_album_artist_position')),
    sa.ForeignKeyConstraint(['album_id'], ['album.id'], name=op.f('fk_album_artist_album_id_album'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['artist_id'], ['artist.id'], name=op.f('fk_album_artist_artist_id_artist'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('album_id', 'artist_id', name=op.f('pk_album_artist')),
    sa.UniqueConstraint('album_id', 'position', name=op.f('uq_album_artist_album_id'))
    )
    op.create_table('track',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('audio_asset_id', sa.Uuid(), nullable=False),
    sa.Column('content_sha256', sa.String(length=64), nullable=False),
    sa.Column('album_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('duration_ms', sa.Integer(), nullable=False),
    sa.Column('track_number', sa.Integer(), nullable=True),
    sa.Column('metadata_sources', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('revision', sa.Integer(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name=op.f('ck_track_hash')),
    sa.CheckConstraint('duration_ms > 0', name=op.f('ck_track_duration')),
    sa.CheckConstraint('length(trim(title)) > 0', name=op.f('ck_track_title')),
    sa.CheckConstraint('revision > 0', name=op.f('ck_track_revision')),
    sa.CheckConstraint('track_number IS NULL OR track_number > 0', name=op.f('ck_track_number')),
    sa.ForeignKeyConstraint(['album_id'], ['album.id'], name=op.f('fk_track_album_id_album'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['audio_asset_id'], ['media_asset.id'], name=op.f('fk_track_audio_asset_id_media_asset'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_track')),
    sa.UniqueConstraint('audio_asset_id', name=op.f('uq_track_audio_asset_id')),
    sa.UniqueConstraint('content_sha256', name=op.f('uq_track_content_sha256'))
    )
    op.create_index(op.f('ix_track_album_id'), 'track', ['album_id'], unique=False)
    op.create_table('playlist_track',
    sa.Column('playlist_id', sa.Uuid(), nullable=False),
    sa.Column('track_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('position >= 0', name=op.f('ck_playlist_track_position')),
    sa.ForeignKeyConstraint(['playlist_id'], ['playlist.id'], name=op.f('fk_playlist_track_playlist_id_playlist'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['track_id'], ['track.id'], name=op.f('fk_playlist_track_track_id_track'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('playlist_id', 'track_id', name=op.f('pk_playlist_track')),
    sa.UniqueConstraint('playlist_id', 'position', name=op.f('uq_playlist_track_playlist_id'))
    )
    op.create_table('track_artist',
    sa.Column('track_id', sa.Uuid(), nullable=False),
    sa.Column('artist_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('position >= 0', name=op.f('ck_track_artist_position')),
    sa.ForeignKeyConstraint(['artist_id'], ['artist.id'], name=op.f('fk_track_artist_artist_id_artist'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['track_id'], ['track.id'], name=op.f('fk_track_artist_track_id_track'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('track_id', 'artist_id', name=op.f('pk_track_artist')),
    sa.UniqueConstraint('track_id', 'position', name=op.f('uq_track_artist_track_id'))
    )
    op.execute(sa.text(
        "INSERT INTO album (id, title, system_key) "
        "VALUES ('00000000-0000-4000-8000-000000000005', 'Sin álbum', 'unknown')"
    ))


def downgrade():
    op.drop_table('track_artist')
    op.drop_table('playlist_track')
    op.drop_index(op.f('ix_track_album_id'), table_name='track')
    op.drop_table('track')
    op.drop_table('album_artist')
    op.drop_table('playlist')
    op.drop_table('album')
    op.drop_index(op.f('ix_media_asset_sha256'), table_name='media_asset')
    op.drop_table('media_asset')
    op.drop_table('artist')
