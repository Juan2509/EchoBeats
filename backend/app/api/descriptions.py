from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from app.api.metadata import engine_for, response
from app.services import descriptions
from app.services import indexing

router = APIRouter()
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255, pattern=r'^[^\x00]*$')]
Evidence = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000, pattern=r'^[^\x00]*$')]


class Feature(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Literal['tempo_bpm', 'timbre', 'instruments', 'energy', 'mood', 'genre', 'context', 'mode', 'percussion', 'voice', 'note_density']
    value: Short
    source: Literal['manual', 'verified', 'metadata']
    evidence: Evidence
    interpretation: bool = Field(strict=True)

    @model_validator(mode='after')
    def valid_feature(self):
        if self.name in {'mood', 'energy', 'context'} and not self.interpretation:
            raise ValueError('Emoción, energía y contexto se registran como interpretaciones.')
        if self.interpretation and self.source != 'manual':
            raise ValueError('Una interpretación debe identificarse como manual.')
        if self.name == 'tempo_bpm':
            try:
                bpm = float(self.value)
            except ValueError:
                raise ValueError('BPM no válido.') from None
            if not 1 <= bpm <= 400:
                raise ValueError('BPM fuera de rango.')
        return self


class DescriptionInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: Annotated[str, StringConstraints(strip_whitespace=True, max_length=6000, pattern=r'^[^\x00]*$')]
    features: Annotated[list[Feature], Field(max_length=20)]
    source: Literal['manual', 'verified', 'metadata']
    source_details: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000, pattern=r'^[^\x00]*$')]

    @model_validator(mode='after')
    def unique_features(self):
        if len({f.name for f in self.features}) != len(self.features):
            raise ValueError('No repetir atributos; combinar sus valores y evidencias.')
        return self


@router.get('/tracks/{track_id}/description')
def get(track_id: UUID, request: Request):
    with engine_for(request).connect() as connection:
        record, token = descriptions.data(connection, track_id)
        state = indexing.state(connection, track_id, request.app.state.settings, record)
        record.update(index_status=state['status'], needs_indexing=record['can_index'] and state['status']!='ready',
            index_notice='Embedding vigente para esta ficha y modelo.' if state['status']=='ready' else 'Sin embedding vigente. Consulta el estado de indexación; corregir la ficha exige un vector de la nueva versión.')
        return response((record, token))


@router.put('/tracks/{track_id}/description')
def put(track_id: UUID, body: DescriptionInput, request: Request,
        if_match: str | None = Header(None), if_none_match: str | None = Header(None)):
    record, token = descriptions.save(engine_for(request), track_id, body.model_dump(), if_match, if_none_match)
    with engine_for(request).connect() as connection:
        state = indexing.state(connection, track_id, request.app.state.settings, record)
    record.update(index_status=state['status'], needs_indexing=record['can_index'] and state['status']!='ready',
        index_notice='Embedding vigente para esta ficha y modelo.' if state['status']=='ready' else 'Sin embedding vigente. Consulta el estado de indexación; corregir la ficha exige un vector de la nueva versión.')
    return response((record, token))


@router.get('/tracks/{track_id}/description/versions/{version}')
def historical(track_id: UUID, version: Annotated[int, Field(ge=1)], request: Request):
    with engine_for(request).connect() as connection:
        return response(descriptions.history(connection, track_id, version))
