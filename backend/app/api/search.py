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


class SearchInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    query: Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=1000,pattern=r'^[^\x00]*$')]
    limit: Annotated[int,Field(strict=True,ge=1,le=20)]=5
    mode: Literal['semantic','lexical','hybrid']='hybrid'
    album_id: UUID | None=None
    playlist_id: UUID | None=None
    explain: bool = Field(default=False,strict=True)


@router.post('/explore/search')
async def search(body:SearchInput,request:Request):
    data=await service.search(engine_for(request),request.app.state.settings,request.app.state.ai_provider,
        body.query,body.mode,body.limit,body.album_id,body.playlist_id)
    data=await exploration.explain(engine_for(request),request.app.state.settings,request.app.state.ai_provider,data,body.explain,body.album_id,body.playlist_id)
    return JSONResponse(jsonable_encoder(data),headers={'Cache-Control':'no-store'})


class SimilarInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    track_id: UUID
    limit: Annotated[int,Field(strict=True,ge=1,le=20)]=5
    album_id: UUID | None=None
    playlist_id: UUID | None=None
    explain: bool = Field(default=False,strict=True)


@router.post('/explore/similar')
async def similar_explained(body:SimilarInput,request:Request):
    data=await run_in_threadpool(service.similar,engine_for(request),request.app.state.settings,body.track_id,body.limit,body.album_id,body.playlist_id)
    data=await exploration.explain(engine_for(request),request.app.state.settings,request.app.state.ai_provider,data,body.explain,body.album_id,body.playlist_id)
    return JSONResponse(jsonable_encoder(data),headers={'Cache-Control':'no-store'})


@router.get('/tracks/{track_id}/similar')
def similar(track_id:UUID,request:Request,limit:Annotated[int,Query(ge=1,le=20)]=5,album_id:UUID | None=None,playlist_id:UUID | None=None):
    data=service.similar(engine_for(request),request.app.state.settings,track_id,limit,album_id,playlist_id)
    return JSONResponse(jsonable_encoder(data),headers={'Cache-Control':'no-store'})
