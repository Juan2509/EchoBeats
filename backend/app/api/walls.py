"""Contrato del muro v1. El editor visual se incorpora en P13–P16."""
from math import cos, radians, sin
from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.api.metadata import engine_for, response
from app.integrations.storage import MediaStore
from app.services import walls

router = APIRouter()
# Unidades del lienzo de referencia 1000 × 700, no porcentajes del viewport.
GEOMETRY_TOLERANCE = 1e-7
Finite = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Unit = Annotated[Finite, Field(ge=0, le=1)]
Size = Annotated[Finite, Field(ge=0.03, le=0.60)]


class Element(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID
    asset_id: UUID
    kind: Literal['poster', 'sticker', 'image', 'gif']
    cx: Unit
    cy: Unit
    width: Size
    height: Size
    rotation_deg: Finite
    z_index: Annotated[int, Field(strict=True, ge=0, le=29)]

    @field_validator('rotation_deg')
    @classmethod
    def normalized_rotation(cls, value):
        return (value + 180) % 360 - 180

    @model_validator(mode='after')
    def rotated_bounds(self):
        angle = radians(self.rotation_deg)
        bx = (abs(self.width * 1000 * cos(angle)) + abs(self.height * 700 * sin(angle))) / 2
        by = (abs(self.width * 1000 * sin(angle)) + abs(self.height * 700 * cos(angle))) / 2
        x, y, tolerance = self.cx * 1000, self.cy * 700, GEOMETRY_TOLERANCE
        if not (bx - tolerance <= x <= 1000 - bx + tolerance and by - tolerance <= y <= 700 - by + tolerance):
            raise ValueError('El elemento girado debe quedar completamente dentro del muro.')
        return self


class Composition(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Annotated[int, Field(strict=True, ge=1, le=1)]
    background_color: Annotated[str, Field(pattern=r'^#[0-9A-Fa-f]{6}$')]
    elements: Annotated[list[Element], Field(max_length=30)]

    @field_validator('background_color')
    @classmethod
    def normalize_color(cls, value):
        return value.upper()

    @field_validator('elements')
    @classmethod
    def unique_ids(cls, values):
        if len({item.id for item in values}) != len(values):
            raise ValueError('Los IDs de elementos no deben repetirse.')
        return values


@router.get('/albums/{album_id}/wall')
def get_wall(album_id: UUID, request: Request):
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        return response(walls.data(connection, album_id))


@router.put('/albums/{album_id}/wall')
def put_wall(album_id: UUID, composition: Composition, request: Request, if_match: str | None = Header(None)):
    return response(walls.replace(engine_for(request), MediaStore(request.app.state.settings.media_root),
                                  album_id, composition.model_dump(), if_match))


@router.post('/albums/{album_id}/wall/reset')
def reset_wall(album_id: UUID, request: Request, if_match: str | None = Header(None)):
    return response(walls.reset(engine_for(request), MediaStore(request.app.state.settings.media_root), album_id, if_match))
