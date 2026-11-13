from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from app.api.metadata import engine_for
from app.models.catalog import processing_job
from app.services import processing
from app.services.metadata import require_track

router = APIRouter()


class ProcessingCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation: Literal['prepare_metadata'] = 'prepare_metadata'


def response(data, status=200):
    return JSONResponse(jsonable_encoder(data), status_code=status, headers={'Cache-Control': 'no-store'})


@router.post('/tracks/{track_id}/processing-jobs', status_code=202)
def create(track_id: UUID, body: ProcessingCreate, request: Request):
    return response(processing.enqueue(engine_for(request), track_id), 202)


@router.get('/tracks/{track_id}/processing-jobs')
def listing(track_id: UUID, request: Request):
    with engine_for(request).connect() as connection:
        current = require_track(connection, track_id)
        rows = connection.execute(select(processing_job).where(processing_job.c.track_id == track_id).order_by(processing_job.c.created_at.desc(), processing_job.c.id.desc()).limit(10))
        return response({'items': [processing.public(row, current.revision) for row in rows], 'limit': 10})


@router.get('/jobs/{job_id}')
def get(job_id: UUID, request: Request):
    with engine_for(request).connect() as connection:
        row = processing.require_job(connection, job_id)
        return response(processing.public(row, require_track(connection, row.track_id).revision))


@router.post('/jobs/{job_id}/retry', status_code=202)
def retry(job_id: UUID, request: Request):
    return response(processing.retry(engine_for(request), job_id), 202)
