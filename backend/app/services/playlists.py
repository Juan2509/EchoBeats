"""Playlists versionadas; editar una lista nunca modifica sus pistas o álbumes."""
from sqlalchemy import func, select
from app.models.catalog import playlist, playlist_track, track
from app.services.metadata import MetadataError, check_revision, etag, require_cover, track_data


def require_playlist(connection, identity, lock=False):
    statement = select(playlist).where(playlist.c.id == identity)
    row = connection.execute(statement.with_for_update() if lock else statement).first()
    if row is None:
        raise MetadataError('playlist_not_found', 'No existe esa playlist.', 404)
    return row


def data(connection, identity, include_items=True):
    row = require_playlist(connection, identity)
    ids = connection.scalars(select(playlist_track.c.track_id).where(
        playlist_track.c.playlist_id == identity).order_by(playlist_track.c.position)).all()
    result = {key: getattr(row, key) for key in ('id', 'name', 'appearance', 'image_asset_id', 'revision')}
    result.update(image_url=f'/api/v1/assets/{row.image_asset_id}/content' if row.image_asset_id else None, track_count=len(ids))
    if include_items:
        result['items'] = [track_data(connection, value)[0] for value in ids]
    return result, etag('playlist', row)


def create(engine, values):
    with engine.begin() as connection:
        require_cover(connection, values.get('image_asset_id'))
        identity = connection.scalar(playlist.insert().values(**values).returning(playlist.c.id))
        return data(connection, identity)


def update(engine, identity, values, expected, ids=None):
    with engine.begin() as connection:
        row = require_playlist(connection, identity, lock=True)
        check_revision('playlist', row, expected)
        if 'image_asset_id' in values:
            require_cover(connection, values['image_asset_id'])
        if ids is not None:
            existing = set(connection.scalars(select(track.c.id).where(track.c.id.in_(ids))).all())
            if existing != set(ids):
                raise MetadataError('invalid_tracks', 'Una de las canciones ya no existe. Recarga la biblioteca.')
            connection.execute(playlist_track.delete().where(playlist_track.c.playlist_id == identity))
            if ids:
                connection.execute(playlist_track.insert(), [dict(playlist_id=identity, track_id=value, position=index) for index, value in enumerate(ids)])
        connection.execute(playlist.update().where(playlist.c.id == identity).values(**values, revision=row.revision + 1, updated_at=func.now()))
        return data(connection, identity)
