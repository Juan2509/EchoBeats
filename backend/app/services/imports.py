"""Importación por archivo: validar, deduplicar y confirmar archivo + catálogo."""

from pathlib import Path
import wave
from uuid import uuid4

from mutagen import MutagenError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.integrations.storage import FileTooLarge, MediaStore
from app.integrations.audio_formats import AUDIO_MIME_TYPES, SUPPORTED_AUDIO, inspect_audio
from app.models.catalog import UNKNOWN_ALBUM_ID, media_asset, track


def safe_filename(filename: str | None) -> str:
    name = (filename or "archivo.mp3").replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(char for char in name if ord(char) >= 32 and char != "\x7f")
    return name[:255] or "archivo.mp3"


def rejected(filename, code, message):
    return {"file_name": filename, "status": "rejected", "error": {"code": code, "message": message}}


def import_file(engine, store: MediaStore, stream, filename: str | None, max_bytes: int):
    name = safe_filename(filename)
    extension = Path(name).suffix.lower()
    if extension not in AUDIO_MIME_TYPES:
        return rejected(name, "unsupported_format", f"Formatos admitidos: {SUPPORTED_AUDIO} (.mp3, .wav, .flac, .ogg, .opus).")
    try:
        with store.stage(stream, max_bytes) as (staged, digest, size):
            try:
                info = inspect_audio(staged, extension)
            except (MutagenError, ValueError, EOFError, wave.Error):
                return rejected(name, "invalid_audio", f"Audio no válido, incompleto o extensión/códec incompatible. Se admite {SUPPORTED_AUDIO}.")
            return persist_file(engine, store, staged, digest, size, info.duration_ms, name, info.extension, info.mime_type)
    except FileTooLarge:
        return rejected(name, "file_too_large", "El audio supera el tamaño máximo permitido.")
    except (OSError, ValueError):
        return rejected(name, "storage_unavailable", "No se pudo guardar el archivo. Puedes reintentar la importación.")
    except SQLAlchemyError:
        return rejected(name, "database_unavailable", "No se pudo confirmar el registro. Reintenta cuando la base esté disponible.")


def persist_file(engine, store, staged, digest, size, duration_ms, name, extension='.mp3', mime_type='audio/mpeg'):
    asset_id, track_id = uuid4(), uuid4()
    key = f"audio/{asset_id.hex}{extension}"
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
                original_name=name, mime_type=mime_type, byte_size=size,
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
