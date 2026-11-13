from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Header, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.api.metadata import Name, SearchText, engine_for, response
from app.services import library, playlists

router = APIRouter()


class PlaylistCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Name
    appearance: Literal['vinyl', 'image'] = 'vinyl'
    image_asset_id: UUID | None = None

    @field_validator('name')
    @classmethod
    def valid_name(cls, value):
        if value is None:
            return value
        if '\x00' in value:
            raise ValueError('Nombre no válido.')
        value.encode('utf-8')
        return value


class PlaylistPatch(PlaylistCreate):
    name: Name | None = None
    appearance: Literal['vinyl', 'image'] | None = None

    @field_validator('name', 'appearance')
    @classmethod
    def non_null(cls, value):
        if value is None:
            raise ValueError('Este campo no admite null.')
        return value


class Tracks(BaseModel):
    model_config = ConfigDict(extra='forbid')
    track_ids: list[UUID] = Field(max_length=1000)

    @field_validator('track_ids')
    @classmethod
    def unique(cls, values):
        if len(set(values)) != len(values):
            raise ValueError('Una canción solo puede aparecer una vez.')
        return values


@router.get('/playlists')
def listing(request: Request, q: SearchText = '', limit: int = Query(24, ge=1, le=100), offset: int = Query(0, ge=0)):
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        return library.page(connection, 'playlists', limit, offset, q)


@router.post('/playlists')
def create(body: PlaylistCreate, request: Request):
    return response(playlists.create(engine_for(request), body.model_dump()), 201)


@router.get('/playlists/{identity}')
def detail(identity: UUID, request: Request):
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        return response(playlists.data(connection, identity))


@router.patch('/playlists/{identity}')
def patch(identity: UUID, body: PlaylistPatch, request: Request, if_match: str | None = Header(None)):
    return response(playlists.update(engine_for(request), identity, body.model_dump(exclude_unset=True), if_match))


@router.put('/playlists/{identity}/tracks')
def replace(identity: UUID, body: Tracks, request: Request, if_match: str | None = Header(None)):
    return response(playlists.update(engine_for(request), identity, {}, if_match, body.track_ids))
