"""Estados explícitos e idempotentes: no alternar mediante un GET ni guardar escuchas."""
from uuid import UUID
from fastapi import APIRouter, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.api.metadata import engine_for, SearchText
from app.models.catalog import favorite, track
from app.services import library, metadata

router = APIRouter()


class FavoriteInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    favorite: bool = Field(strict=True)


def exists(connection, track_id, lock=False):
    statement = select(track.c.id).where(track.c.id == track_id)
    if lock:
        statement = statement.with_for_update()
    if connection.scalar(statement) is None:
        raise metadata.MetadataError('track_not_found', 'La canción no existe.', 404)


def state(connection, track_id):
    saved = connection.scalar(select(favorite.c.created_at).where(favorite.c.track_id == track_id))
    return {'track_id': track_id, 'favorite': saved is not None, 'created_at': saved}


def response(data):
    return JSONResponse(jsonable_encoder(data), headers={'Cache-Control': 'no-store'})


@router.get('/tracks/{track_id}/favorite')
def get_favorite(track_id: UUID, request: Request):
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        exists(connection, track_id)
        return response(state(connection, track_id))


@router.put('/tracks/{track_id}/favorite')
def set_favorite(track_id: UUID, body: FavoriteInput, request: Request):
    with engine_for(request).begin() as connection:
        # Serializa cambios de una pista incluso cuando todavía no hay fila favorita.
        exists(connection, track_id, lock=True)
        if body.favorite:
            connection.execute(insert(favorite).values(track_id=track_id).on_conflict_do_nothing())
        else:
            connection.execute(favorite.delete().where(favorite.c.track_id == track_id))
        data = state(connection, track_id)
    return response(data)


@router.get('/favorites')
def favorites(request: Request, limit: int = Query(24, ge=1, le=100), offset: int = Query(0, ge=0), q: SearchText = ''):
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        return response(library.page(connection, 'tracks', limit, offset, q, favorites_only=True))
