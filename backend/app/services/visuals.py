"""Publicación atómica de recurso y preview, con deduplicación y conservación."""
import hashlib
from io import BytesIO
from uuid import uuid4
from sqlalchemy import select, text
from app.integrations.visuals import MAX_BYTES, prepare_visual
from app.models.catalog import media_asset
from app.services.covers import publications, save_cover
from app.services.metadata import MetadataError


def upload_visual(engine, store, stream):
    try:
        visual = prepare_visual(stream.read(MAX_BYTES + 1))
    except ValueError as exc:
        raise MetadataError('invalid_visual', str(exc)) from None
    kind = 'gif' if visual.mime_type == 'image/gif' else 'image'
    digest = hashlib.sha256(visual.data).hexdigest()
    try:
        with publications(engine, store) as created:
            with engine.begin() as connection:
                connection.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int.from_bytes(bytes.fromhex(digest)[:8], 'big', signed=True)})
                existing = connection.execute(select(media_asset).where(media_asset.c.kind == kind, media_asset.c.sha256 == digest)).first()
                if existing:
                    asset_id, key, preview_id = existing.id, existing.storage_key, existing.static_preview_id
                else:
                    asset_id = uuid4()
                    key = f'images/{asset_id.hex}.{"gif" if kind == "gif" else "png"}'
                    preview_id = None
                # Orden de locks: visual -> portada. Las portadas no adquieren locks de visuales.
                if visual.preview:
                    preview_id = save_cover(connection, store, visual.preview, created)
                if existing is None:
                    created.append((asset_id, key))
                    connection.execute(media_asset.insert().values(id=asset_id, kind=kind, storage_key=key,
                        sha256=digest, original_name='decoracion.gif' if kind == 'gif' else 'decoracion.png',
                        mime_type=visual.mime_type, byte_size=len(visual.data), width_px=visual.width,
                        height_px=visual.height, frame_count=visual.frames, static_preview_id=preview_id))
                elif preview_id != existing.static_preview_id:
                    connection.execute(media_asset.update().where(media_asset.c.id == asset_id).values(static_preview_id=preview_id))
                if not existing or not store.path_for(key).is_file():
                    with store.stage(BytesIO(visual.data), MAX_BYTES) as (staged, _, _):
                        store.publish(staged, key)
    except (OSError, ValueError):
        raise MetadataError('visual_storage_unavailable', 'No se pudo guardar el recurso visual. La composición de la pared se conserva.', 503) from None
    return {'id': asset_id, 'mime_type': visual.mime_type, 'width_px': visual.width, 'height_px': visual.height,
            'frame_count': visual.frames, 'content_url': f'/api/v1/assets/{asset_id}/content',
            'static_preview_url': f'/api/v1/assets/{preview_id}/content' if preview_id else None}
