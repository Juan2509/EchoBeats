from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Request, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StringConstraints, Field
from app.api.metadata import engine_for
from app.services import search as service
from app.services import exploration
from starlette.concurrency import run_in_threadpool

router=APIRouter()
PreferenceMode=Literal['off','favorites','discovery']

class ChatMessage(BaseModel):
    model_config=ConfigDict(extra='forbid')
    role: Literal['user','assistant']
    content: Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=1000,pattern=r'^[^\x00]*$')]

class ChatInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    messages: list[ChatMessage]=Field(min_length=1,max_length=9)
    current_track_id: UUID | None=None
    recent_track_ids: list[UUID]=Field(default_factory=list,max_length=12)
    previous_track_ids: list[UUID]=Field(default_factory=list,max_length=20)
    reference_track_id: UUID | None=None
    use_ai: bool=Field(default=False,strict=True)

@router.get('/explore/chat/status')
async def chat_status(request: Request):
    settings = request.app.state.settings
    cloud = settings.ai_enabled and bool(settings.openai_api_key.get_secret_value().strip())
    return JSONResponse(
        {'cloud_enabled': settings.ai_enabled, 'cloud_ready': cloud},
        headers={'Cache-Control': 'no-store'},
    )


@router.post('/explore/chat')
async def chat(body:ChatInput,request:Request):
    from app.services.music_chat import respond
    if body.messages[-1].role!='user':
        from app.services.metadata import MetadataError
        raise MetadataError('chat_message','El último mensaje debe ser tu pregunta.')
    result=await respond(engine_for(request),request.app.state.settings,request.app.state.ai_provider,
        [m.model_dump() for m in body.messages],body.current_track_id,body.recent_track_ids,body.reference_track_id,body.use_ai,body.previous_track_ids)
    return JSONResponse(jsonable_encoder(result),headers={'Cache-Control':'no-store'})


class SearchInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    query: Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=1000,pattern=r'^[^\x00]*$')]
    limit: Annotated[int,Field(strict=True,ge=1,le=20)]=5
    mode: Literal['semantic','lexical','hybrid']='hybrid'
    album_id: UUID | None=None
    playlist_id: UUID | None=None
    explain: bool = Field(default=False,strict=True)
    preferences: PreferenceMode = 'off'


@router.post('/explore/search')
async def search(body:SearchInput,request:Request):
    data=await service.search(engine_for(request),request.app.state.settings,request.app.state.ai_provider,
        body.query,body.mode,body.limit,body.album_id,body.playlist_id,body.preferences)
    data=await exploration.explain(engine_for(request),request.app.state.settings,request.app.state.ai_provider,data,body.explain,body.album_id,body.playlist_id)
    return JSONResponse(jsonable_encoder(data),headers={'Cache-Control':'no-store'})


class SimilarInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    track_id: UUID
    limit: Annotated[int,Field(strict=True,ge=1,le=20)]=5
    album_id: UUID | None=None
    playlist_id: UUID | None=None
    explain: bool = Field(default=False,strict=True)
    preferences: PreferenceMode = 'off'


@router.post('/explore/similar')
async def similar_explained(body:SimilarInput,request:Request):
    data=await run_in_threadpool(service.similar,engine_for(request),request.app.state.settings,body.track_id,body.limit,body.album_id,body.playlist_id,body.preferences)
    data=await exploration.explain(engine_for(request),request.app.state.settings,request.app.state.ai_provider,data,body.explain,body.album_id,body.playlist_id)
    return JSONResponse(jsonable_encoder(data),headers={'Cache-Control':'no-store'})


@router.get('/tracks/{track_id}/similar')
def similar(track_id:UUID,request:Request,limit:Annotated[int,Query(ge=1,le=20)]=5,album_id:UUID | None=None,playlist_id:UUID | None=None,preferences:PreferenceMode='off'):
    data=service.similar(engine_for(request),request.app.state.settings,track_id,limit,album_id,playlist_id,preferences)
    return JSONResponse(jsonable_encoder(data),headers={'Cache-Control':'no-store'})


@router.get('/tracks/{track_id}/audio-similar')
def audio_similar(track_id: UUID, request: Request, limit: Annotated[int, Query(ge=1, le=20)] = 5):
    from app.services.audio_similarity import similar_audio

    data = similar_audio(engine_for(request), track_id, limit)
    return JSONResponse(jsonable_encoder(data), headers={'Cache-Control': 'no-store'})


@router.get('/tracks/{track_id}/audio-index')
def audio_index_status(track_id: UUID, request: Request):
    from app.services.audio_similarity import audio_index_status as status

    data = status(engine_for(request), track_id, request.app.state.settings.processing_worker_enabled)
    return JSONResponse(data, headers={'Cache-Control': 'no-store'})


@router.post('/tracks/{track_id}/audio-index/retry')
def audio_index_retry(track_id: UUID, request: Request):
    from app.services.audio_similarity import retry_audio_index

    data = retry_audio_index(engine_for(request), track_id, request.app.state.settings.processing_worker_enabled)
    return JSONResponse(data, headers={'Cache-Control': 'no-store'})
