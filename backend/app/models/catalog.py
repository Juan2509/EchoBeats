"""Catálogo persistente local. Los muros y la IA se añaden en pasos posteriores."""

from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger, CheckConstraint, Column, DateTime, ForeignKey, Integer,
    MetaData, String, Table, UniqueConstraint, Uuid, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(naming_convention={
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})
UNKNOWN_ALBUM_ID = UUID("00000000-0000-4000-8000-000000000005")


def identity():
    return Column("id", Uuid, primary_key=True, default=uuid4)


def timestamps():
    return [
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    ]


media_asset = Table(
    "media_asset", metadata, identity(),
    Column("kind", String(16), nullable=False),
    Column("storage_key", String(255), nullable=False, unique=True),
    Column("sha256", String(64), nullable=False, index=True),
    Column("original_name", String(255), nullable=False),
    Column("mime_type", String(80), nullable=False),
    Column("byte_size", BigInteger, nullable=False),
    Column("width_px", Integer), Column("height_px", Integer), Column("frame_count", Integer),
    Column("static_preview_id", Uuid, ForeignKey("media_asset.id", ondelete="RESTRICT")),
    *timestamps(),
    CheckConstraint("kind IN ('audio','image','gif','cover')", name="kind"),
    CheckConstraint("byte_size > 0", name="size"),
    CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="hash"),
    CheckConstraint("storage_key ~ '^(audio|images)/[0-9a-f]{32}\\.(mp3|wav|flac|ogg|opus|png|jpg|jpeg|gif)$'", name="key"),
    CheckConstraint("width_px IS NULL OR width_px > 0", name="width"),
    CheckConstraint("height_px IS NULL OR height_px > 0", name="height"),
    CheckConstraint("frame_count IS NULL OR frame_count > 0", name="frames"),
    CheckConstraint("static_preview_id IS NULL OR static_preview_id <> id", name="preview"),
)
artist = Table(
    "artist", metadata, identity(), Column("name", String(255), nullable=False),
    Column("normalized_name", String(320), nullable=False, unique=True),
    CheckConstraint("length(trim(name)) > 0", name="name"),
    CheckConstraint("length(trim(normalized_name)) > 0", name="normalized_name"),
)
album = Table(
    "album", metadata, identity(), Column("title", String(255), nullable=False),
    Column("cover_asset_id", Uuid, ForeignKey("media_asset.id", ondelete="RESTRICT")),
    Column("system_key", String(32), unique=True),
    Column("import_key", String(64), unique=True),
    Column("metadata_sources", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("revision", Integer, nullable=False, server_default="1"), *timestamps(),
    CheckConstraint("length(trim(title)) > 0", name="title"),
    CheckConstraint("revision > 0", name="revision"),
    CheckConstraint("system_key IS NULL OR (system_key = 'unknown' AND title = 'Sin álbum')", name="system_album"),
)
album_artist = Table(
    "album_artist", metadata,
    Column("album_id", Uuid, ForeignKey("album.id", ondelete="RESTRICT"), primary_key=True),
    Column("artist_id", Uuid, ForeignKey("artist.id", ondelete="RESTRICT"), primary_key=True),
    Column("position", Integer, nullable=False),
    UniqueConstraint("album_id", "position"), CheckConstraint("position >= 0", name="position"),
)
track = Table(
    "track", metadata, identity(),
    Column("audio_asset_id", Uuid, ForeignKey("media_asset.id", ondelete="RESTRICT"), nullable=False, unique=True),
    Column("content_sha256", String(64), nullable=False, unique=True),
    Column("album_id", Uuid, ForeignKey("album.id", ondelete="RESTRICT"), nullable=False, index=True),
    Column("cover_asset_id", Uuid, ForeignKey("media_asset.id", ondelete="RESTRICT")),
    Column("title", String(255), nullable=False),
    Column("duration_ms", Integer, nullable=False), Column("track_number", Integer),
    Column("metadata_sources", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("revision", Integer, nullable=False, server_default="1"), *timestamps(),
    CheckConstraint("duration_ms > 0", name="duration"),
    CheckConstraint("length(trim(title)) > 0", name="title"),
    CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name="hash"),
    CheckConstraint("track_number IS NULL OR track_number > 0", name="number"),
    CheckConstraint("revision > 0", name="revision"),
)
track_artist = Table(
    "track_artist", metadata,
    Column("track_id", Uuid, ForeignKey("track.id", ondelete="RESTRICT"), primary_key=True),
    Column("artist_id", Uuid, ForeignKey("artist.id", ondelete="RESTRICT"), primary_key=True),
    Column("position", Integer, nullable=False),
    UniqueConstraint("track_id", "position"), CheckConstraint("position >= 0", name="position"),
)
playlist = Table(
    "playlist", metadata, identity(), Column("name", String(255), nullable=False),
    Column("appearance", String(16), nullable=False, server_default="vinyl"),
    Column("image_asset_id", Uuid, ForeignKey("media_asset.id", ondelete="RESTRICT")),
    Column("revision", Integer, nullable=False, server_default="1"), *timestamps(),
    CheckConstraint("length(trim(name)) > 0", name="name"),
    CheckConstraint("appearance IN ('vinyl','image')", name="appearance"),
    CheckConstraint("revision > 0", name="revision"),
)
playlist_track = Table(
    "playlist_track", metadata,
    Column("playlist_id", Uuid, ForeignKey("playlist.id", ondelete="RESTRICT"), primary_key=True),
    Column("track_id", Uuid, ForeignKey("track.id", ondelete="RESTRICT"), primary_key=True),
    Column("position", Integer, nullable=False),
    UniqueConstraint("playlist_id", "position"), CheckConstraint("position >= 0", name="position"),
)
