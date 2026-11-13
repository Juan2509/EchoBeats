"""Lectura y edición de fichas; la fuente manual tiene prioridad por campo."""

import hashlib
import json
from mutagen import MutagenError

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from app.integrations.tags import normalized, read_tags
from app.models.catalog import UNKNOWN_ALBUM_ID, album, album_artist, artist, media_asset, track, track_artist
from app.services.covers import publications, save_cover


class MetadataError(Exception):
    def __init__(self, code, message, status=422, *, current_revision=None, current_etag=None):
        self.code, self.message, self.status = code, message, status
        self.current_revision, self.current_etag = current_revision, current_etag


def etag(kind, row):
    return f'"{kind}-{row.id}-{row.revision}"'


def check_revision(kind, row, expected):
    if expected is None:
        raise MetadataError("revision_required", "Falta la revisión del recurso. Recarga los datos antes de guardar.", 428)
    if expected != etag(kind, row):
        raise MetadataError("revision_conflict", "Los datos cambiaron en otra pestaña. Recarga para revisar tus cambios.", 412, current_revision=row.revision, current_etag=etag(kind, row))


def artist_ids(connection, names):
    resolved = {}
    for name in sorted(names, key=normalized):
        key = normalized(name)
        found = connection.scalar(insert(artist).values(name=name, normalized_name=key).on_conflict_do_nothing(
            index_elements=[artist.c.normalized_name],
        ).returning(artist.c.id))
        if found is None:
            found = connection.scalar(select(artist.c.id).where(artist.c.normalized_name == key))
        resolved[key] = found
    return [resolved[normalized(name)] for name in names]


def replace_credits(connection, table, parent_column, parent_id, ids):
    connection.execute(table.delete().where(parent_column == parent_id))
    if ids:
        connection.execute(table.insert(), [
            {parent_column.name: parent_id, "artist_id": value, "position": index}
            for index, value in enumerate(ids)
        ])


def credits(connection, table, column, value):
    return [dict(row._mapping) for row in connection.execute(
        select(artist.c.id, artist.c.name).join(table, artist.c.id == table.c.artist_id)
        .where(column == value).order_by(table.c.position),
    )]


def album_for_tags(connection, tags):
    if not tags.album_title or not tags.album_artists:
        return UNKNOWN_ALBUM_ID
    key = hashlib.sha256(json.dumps([normalized(tags.album_title), [normalized(name) for name in tags.album_artists]]).encode()).hexdigest()
    connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True)})
    found = connection.scalar(select(album.c.id).where(album.c.import_key == key))
    if found is not None:
        return found
    found = connection.scalar(album.insert().values(
        title=tags.album_title, import_key=key, metadata_sources={"title": "file", "artists": "file", "cover": "fallback"},
    ).returning(album.c.id))
    from app.services.walls import create_initial
    create_initial(connection, found)
    replace_credits(connection, album_artist, album_artist.c.album_id, found, artist_ids(connection, tags.album_artists))
    return found


def require_track(connection, track_id, lock=False):
    statement = select(track).where(track.c.id == track_id)
    row = connection.execute(statement.with_for_update() if lock else statement).first()
    if row is None:
        raise MetadataError("track_not_found", "No existe esa canción.", 404)
    return row


def require_album(connection, album_id, lock=False):
    statement = select(album).where(album.c.id == album_id)
    row = connection.execute(statement.with_for_update() if lock else statement).first()
    if row is None:
        raise MetadataError("album_not_found", "No existe ese álbum.", 404)
    return row


def require_cover(connection, asset_id):
    if asset_id is None:
        return
    resource = connection.execute(select(media_asset).where(media_asset.c.id == asset_id)).first()
    if resource is None or resource.kind not in {"cover", "image"} or resource.mime_type not in {"image/png", "image/jpeg"}:
        raise MetadataError("invalid_cover", "La referencia no corresponde a una portada PNG o JPEG válida.")


def track_data(connection, track_id):
    row = require_track(connection, track_id)
    collection = require_album(connection, row.album_id)
    # Un null manual significa usar la portada predeterminada, no heredar.
    cover = row.cover_asset_id
    cover_source = row.metadata_sources.get("cover", "fallback")
    if cover is None and row.metadata_sources.get("cover") != "manual":
        cover = collection.cover_asset_id
        if cover is not None:
            cover_source = "album"
    return {
        "id": row.id, "title": row.title, "artists": credits(connection, track_artist, track_artist.c.track_id, row.id),
        "album_id": row.album_id, "album_title": collection.title, "duration_ms": row.duration_ms,
        "audio_url": f"/api/v1/tracks/{row.id}/audio",
        "audio_mime_type": connection.scalar(select(media_asset.c.mime_type).where(media_asset.c.id == row.audio_asset_id)),
        "track_number": row.track_number, "cover_asset_id": row.cover_asset_id,
        "cover_url": f"/api/v1/assets/{cover}/content" if cover else None,
        "cover_source": cover_source,
        "metadata_sources": row.metadata_sources, "revision": row.revision, "updated_at": row.updated_at,
    }, etag("track", row)


def album_data(connection, album_id):
    row = require_album(connection, album_id)
    return {
        "id": row.id, "title": row.title, "artists": credits(connection, album_artist, album_artist.c.album_id, row.id),
        "cover_asset_id": row.cover_asset_id,
        "cover_url": f"/api/v1/assets/{row.cover_asset_id}/content" if row.cover_asset_id else None,
        "track_count": connection.scalar(select(func.count()).select_from(track).where(track.c.album_id == row.id)),
        "system_key": row.system_key, "metadata_sources": row.metadata_sources, "revision": row.revision,
    }, etag("album", row)


def enrich_track(engine, store, track_id, expected=None):
    with engine.connect() as connection:
        row = require_track(connection, track_id)
        key = connection.scalar(select(media_asset.c.storage_key).where(media_asset.c.id == row.audio_asset_id))
    path = store.path_for(key)
    if not path.is_file():
        raise MetadataError("media_missing", "No se encuentra el audio original para leer las etiquetas.", 404)
    try:
        tags = read_tags(path)
    except (MutagenError, OSError, ValueError):
        raise MetadataError("metadata_unreadable", "No se pudieron leer las etiquetas del original; los datos guardados se conservan.") from None
    with publications(engine, store) as created:
        with engine.begin() as connection:
            row = require_track(connection, track_id, lock=True)
            if expected is not None:
                check_revision("track", row, expected)
            sources = dict(row.metadata_sources)
            values = {}
            for field, value in (("title", tags.title), ("track_number", tags.track_number)):
                if sources.get(field) != "manual" and value is not None:
                    values[field] = value
                    sources[field] = "file"
                elif field not in sources:
                    sources[field] = "fallback"
            if sources.get("artists") != "manual":
                ids = artist_ids(connection, tags.artists)
                current = [value["id"] for value in credits(connection, track_artist, track_artist.c.track_id, row.id)]
                if current != ids:
                    replace_credits(connection, track_artist, track_artist.c.track_id, row.id, ids)
                    values["revision"] = row.revision + 1
                sources["artists"] = "file" if tags.artists else "fallback"
            if sources.get("album") != "manual":
                current_album = require_album(connection, row.album_id)
                manually_named = any(current_album.metadata_sources.get(field) == "manual" for field in ("title", "artists"))
                if manually_named:
                    values["album_id"] = row.album_id
                    sources["album"] = "manual"
                else:
                    values["album_id"] = album_for_tags(connection, tags)
                    sources["album"] = "file" if values["album_id"] != UNKNOWN_ALBUM_ID else "fallback"
            if sources.get("cover") != "manual":
                if tags.cover is not None:
                    values["cover_asset_id"] = save_cover(connection, store, tags.cover, created)
                    sources["cover"] = "file"
                    album_id = values.get("album_id", row.album_id)
                    if album_id != UNKNOWN_ALBUM_ID:
                        connection.execute(album.update().where(
                            album.c.id == album_id, album.c.cover_asset_id.is_(None),
                            func.coalesce(album.c.metadata_sources["cover"].astext, "") != "manual",
                        ).values(
                            cover_asset_id=values["cover_asset_id"], revision=album.c.revision + 1,
                            metadata_sources=album.c.metadata_sources.op("||")({"cover": "file"}), updated_at=func.now(),
                        ))
                elif "cover" not in sources:
                    sources["cover"] = "fallback"
            changed = sources != row.metadata_sources or any(value != getattr(row, field) for field, value in values.items())
            if changed:
                connection.execute(track.update().where(track.c.id == row.id).values(
                    **{key: value for key, value in values.items() if key != "revision"},
                    metadata_sources=sources, revision=row.revision + 1, updated_at=func.now(),
                ))
            data, token = track_data(connection, track_id)
    return data, token, tags.warnings


def patch_track(engine, track_id, changes, expected):
    with engine.begin() as connection:
        row = require_track(connection, track_id, lock=True)
        check_revision("track", row, expected)
        sources = dict(row.metadata_sources)
        values = {key: value for key, value in changes.items() if key != "artist_names"}
        if "album_id" in changes:
            require_album(connection, changes["album_id"])
        if "cover_asset_id" in changes:
            require_cover(connection, changes["cover_asset_id"])
        if "artist_names" in changes:
            replace_credits(connection, track_artist, track_artist.c.track_id, row.id, artist_ids(connection, changes["artist_names"]))
        for field in changes:
            sources[{"artist_names": "artists", "album_id": "album", "cover_asset_id": "cover"}.get(field, field)] = "manual"
        if changes:
            connection.execute(track.update().where(track.c.id == row.id).values(
                **values, metadata_sources=sources, revision=row.revision + 1, updated_at=func.now(),
            ))
        return track_data(connection, row.id)


def create_album(engine, title, names):
    with engine.begin() as connection:
        album_id = connection.scalar(album.insert().values(
            title=title, metadata_sources={"title": "manual", "artists": "manual", "cover": "fallback"},
        ).returning(album.c.id))
        from app.services.walls import create_initial
        create_initial(connection, album_id)
        replace_credits(connection, album_artist, album_artist.c.album_id, album_id, artist_ids(connection, names))
        return album_data(connection, album_id)


def patch_album(engine, album_id, changes, expected):
    with engine.begin() as connection:
        row = require_album(connection, album_id, lock=True)
        check_revision("album", row, expected)
        if row.system_key is not None:
            raise MetadataError("system_album", "El álbum de sistema no se edita. Crea o selecciona otro álbum.")
        sources = dict(row.metadata_sources)
        values = {key: value for key, value in changes.items() if key != "artist_names"}
        if "cover_asset_id" in changes:
            require_cover(connection, changes["cover_asset_id"])
        if "artist_names" in changes:
            replace_credits(connection, album_artist, album_artist.c.album_id, row.id, artist_ids(connection, changes["artist_names"]))
        for field in changes:
            sources[{"artist_names": "artists", "cover_asset_id": "cover"}.get(field, field)] = "manual"
        if changes:
            connection.execute(album.update().where(album.c.id == row.id).values(
                **values, metadata_sources=sources,
                # La clave conserva la agrupación original de importación:
                # nuevas pistas con esas etiquetas usan el nombre ya corregido.
                import_key=row.import_key,
                revision=row.revision + 1, updated_at=func.now(),
            ))
        return album_data(connection, row.id)
