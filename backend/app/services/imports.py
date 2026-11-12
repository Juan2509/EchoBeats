"""Importación por archivo: validar, deduplicar y confirmar archivo + catálogo."""

import math
from pathlib import Path
from uuid import uuid4

from mutagen import MutagenError
from mutagen.mp3 import MP3
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.integrations.storage import FileTooLarge, MediaStore
from app.models.catalog import UNKNOWN_ALBUM_ID, media_asset, track


def safe_filename(filename: str | None) -> str:
    name = (filename or "archivo.mp3").replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(char for char in name if ord(char) >= 32 and char != "\x7f")
    return name[:255] or "archivo.mp3"


def rejected(filename, code, message):
    return {"file_name": filename, "status": "rejected", "error": {"code": code, "message": message}}


def import_file(engine, store: MediaStore, stream, filename: str | None, max_bytes: int):
    name = safe_filename(filename)
    if Path(name).suffix.lower() != ".mp3":
        return rejected(name, "unsupported_format", "Solo se admiten archivos con extensión MP3 y audio MP3 válido.")
    try:
        with store.stage(stream, max_bytes) as (staged, digest, size):
            try:
                info = MP3(staged).info
                if info.layer != 3 or info.sketchy or not math.isfinite(info.length) or info.length <= 0:
                    raise ValueError
                duration_ms = max(1, round(info.length * 1000))
            except (MutagenError, ValueError, EOFError):
                return rejected(name, "invalid_audio", "El archivo no contiene audio MP3 válido o está incompleto.")
            return persist_file(engine, store, staged, digest, size, duration_ms, name)
    except FileTooLarge:
        return rejected(name, "file_too_large", "El MP3 supera el tamaño máximo permitido.")
    except (OSError, ValueError):
        return rejected(name, "storage_unavailable", "No se pudo guardar el archivo. Puedes reintentar la importación.")
    except SQLAlchemyError:
        return rejected(name, "database_unavailable", "No se pudo confirmar el registro. Reintenta cuando la base esté disponible.")


def persist_file(engine, store, staged, digest, size, duration_ms, name):
    asset_id, track_id = uuid4(), uuid4()
    key = f"audio/{asset_id.hex}.mp3"
    published = False
    try:
        with engine.begin() as connection:
            # Serializa importaciones del mismo hash, también entre procesos.
            lock_key = int.from_bytes(bytes.fromhex(digest)[:8], "big", signed=True)
            connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})
            existing = connection.execute(
                select(track.c.id, media_asset.c.storage_key)
                .join(media_asset, track.c.audio_asset_id == media_asset.c.id)
                .where(track.c.content_sha256 == digest)
            ).first()
            if existing:
                # Reponer un medio perdido desde una copia idéntica del original.
                if not store.path_for(existing.storage_key).is_file():
                    store.publish(staged, existing.storage_key)
                return {"file_name": name, "status": "duplicate", "track_id": str(existing.id)}
            connection.execute(media_asset.insert().values(
                id=asset_id, kind="audio", storage_key=key, sha256=digest,
                original_name=name, mime_type="audio/mpeg", byte_size=size,
            ))
            store.publish(staged, key)
            published = True
            connection.execute(track.insert().values(
                id=track_id, audio_asset_id=asset_id, content_sha256=digest,
                album_id=UNKNOWN_ALBUM_ID, title=Path(name).stem.strip()[:255] or "Sin título",
                duration_ms=duration_ms,
                metadata_sources={"title": "fallback", "album": "fallback", "artists": "fallback", "duration": "file"},
            ))
        return {"file_name": name, "status": "imported", "track_id": str(track_id)}
    except Exception:
        # Un fallo al confirmar COMMIT puede ser ambiguo: consultar antes de
        # retirar el medio. Si no hay conexión, conservarlo para reconciliación.
        if published or store.path_for(key).exists():
            try:
                with engine.connect() as connection:
                    confirmed = connection.scalar(select(track.c.id).where(track.c.audio_asset_id == asset_id))
                if confirmed:
                    return {"file_name": name, "status": "imported", "track_id": str(confirmed)}
                store.path_for(key).unlink(missing_ok=True)
            except (SQLAlchemyError, OSError):
                pass
        raise
