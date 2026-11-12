"""Publicación de portadas con limpieza conservadora ante rollback ambiguo."""

from contextlib import contextmanager
import hashlib
from io import BytesIO
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.models.catalog import media_asset


@contextmanager
def publications(engine, store):
    created = []
    try:
        yield created
    except Exception:
        for asset_id, key in created:
            try:
                with engine.connect() as connection:
                    confirmed = connection.scalar(select(media_asset.c.id).where(media_asset.c.id == asset_id))
                if not confirmed:
                    store.path_for(key).unlink(missing_ok=True)
            except (SQLAlchemyError, OSError):
                pass  # Conservar para auditoría si no se puede resolver COMMIT.
        raise


def save_cover(connection, store, cover, created):
    digest = hashlib.sha256(cover.data).hexdigest()
    connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": int.from_bytes(bytes.fromhex(digest)[:8], "big", signed=True)})
    existing = connection.execute(select(media_asset).where(media_asset.c.kind == "cover", media_asset.c.sha256 == digest)).first()
    if existing:
        if not store.path_for(existing.storage_key).is_file():
            with store.stage(BytesIO(cover.data), 5 * 1024 * 1024) as (staged, _, _):
                store.publish(staged, existing.storage_key)
        return existing.id
    asset_id = uuid4()
    key = f"images/{asset_id.hex}.png"
    created.append((asset_id, key))
    connection.execute(media_asset.insert().values(
        id=asset_id, kind="cover", storage_key=key, sha256=digest, original_name="portada.png",
        mime_type="image/png", byte_size=len(cover.data), width_px=cover.width, height_px=cover.height,
    ))
    with store.stage(BytesIO(cover.data), 5 * 1024 * 1024) as (staged, _, _):
        store.publish(staged, key)
    return asset_id
