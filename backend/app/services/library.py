"""Lectura paginada y búsqueda literal del catálogo local."""

from sqlalchemy import func, or_, select

from app.models.catalog import album, album_artist, artist, playlist, track, track_artist
from app.services import metadata


def matches(column, query):
    # El usuario busca texto literal, incluidos %, _ y la barra de escape.
    value = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return column.ilike(f'%{value}%', escape='\\')


def track_filter(query):
    credits = select(track_artist.c.track_id).join(artist).where(matches(artist.c.name, query))
    collections = select(album.c.id).where(matches(album.c.title, query))
    album_credits = select(album_artist.c.album_id).join(artist).where(matches(artist.c.name, query))
    return or_(matches(track.c.title, query), track.c.id.in_(credits),
               track.c.album_id.in_(collections), track.c.album_id.in_(album_credits))


def album_filter(query):
    credits = select(album_artist.c.album_id).join(artist).where(matches(artist.c.name, query))
    songs = select(track.c.album_id).where(track_filter(query))
    return or_(matches(album.c.title, query), album.c.id.in_(credits), album.c.id.in_(songs))


def page(connection, kind, limit, offset, query='', album_id=None, include_empty_system=True):
    table = {'tracks': track, 'albums': album, 'playlists': playlist}[kind]
    statement = select(table.c.id)
    if kind == 'albums' and not include_empty_system:
        statement = statement.where(or_(album.c.system_key.is_(None), album.c.id.in_(select(track.c.album_id))))
    if query:
        statement = statement.where({'tracks': track_filter, 'albums': album_filter,
                                     'playlists': lambda q: matches(playlist.c.name, q)}[kind](query))
    if kind == 'tracks' and album_id is not None:
        statement = statement.where(track.c.album_id == album_id)
    total = connection.scalar(select(func.count()).select_from(statement.subquery()))
    title = table.c.name if kind == 'playlists' else table.c.title
    ordering = [func.lower(title), table.c.id]
    if kind == 'tracks' and album_id is not None:
        ordering.insert(0, track.c.track_number.asc().nulls_last())
    ids = connection.scalars(statement.order_by(*ordering).limit(limit).offset(offset)).all()
    if kind == 'playlists':
        items = [dict(connection.execute(select(playlist.c.id, playlist.c.name, playlist.c.appearance)
                                        .where(playlist.c.id == value)).one()._mapping) for value in ids]
    else:
        reader = metadata.track_data if kind == 'tracks' else metadata.album_data
        items = [reader(connection, value)[0] for value in ids]
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}
