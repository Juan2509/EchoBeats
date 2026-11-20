from typing import Annotated
from uuid import UUID
from urllib.parse import unquote

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StringConstraints
from starlette.concurrency import run_in_threadpool

from app.api.metadata import engine_for
from app.integrations import pdf
from app.services import documents
from app.services.metadata import MetadataError

router = APIRouter(prefix="/documents")


def reply(value, status=200):
    return JSONResponse(jsonable_encoder(value), status_code=status, headers={"Cache-Control": "no-store"})


def require_ai(request):
    if not documents.available(request.app.state.settings):
        raise MetadataError("documents_unavailable", "El flujo documental requiere OpenAI y un modelo de 1536 dimensiones.", 503)


@router.get("")
def listing(request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 50,
            offset: Annotated[int, Query(ge=0)] = 0):
    settings = request.app.state.settings
    enabled = documents.available(settings)
    return reply({
        "items": documents.list_documents(engine_for(request), limit, offset),
        "query_enabled": enabled,
        "upload_enabled": enabled and settings.processing_worker_enabled and pdf.scanner_ready(),
    })


@router.post("", status_code=202)
async def ingest(request: Request, encoded_name: Annotated[str, Header(alias="X-Document-Name", max_length=2400)]):
    require_ai(request)
    if not request.app.state.settings.processing_worker_enabled or not pdf.scanner_ready():
        raise MetadataError("document_scanner_unavailable", "Activa el trabajador y prepara las firmas de ClamAV.", 503)
    try:
        name = unquote(encoded_name, errors="strict")
    except UnicodeError:
        name = ""
    if (not 5 <= len(name) <= 200 or not name.lower().endswith(".pdf") or any(not c.isprintable() for c in name)
            or "/" in name or "\\" in name):
        raise MetadataError("invalid_document_name", "Indica un nombre de archivo PDF válido.", 422)
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/pdf":
        raise MetadataError("invalid_document_type", "Selecciona un archivo PDF.", 415)
    buffer = bytearray()
    async for part in request.stream():
        if len(buffer) + len(part) > pdf.MAX_BYTES:
            raise MetadataError("document_size", "El PDF supera los 10 MiB.", 413)
        buffer.extend(part)
    if not buffer.startswith(b"%PDF-"):
        raise MetadataError("invalid_pdf", "El archivo no tiene una cabecera PDF válida.", 422)
    saved = await run_in_threadpool(documents.create, engine_for(request), name, bytes(buffer))
    return reply(saved, 202)


@router.delete("/{identity}", status_code=204)
def remove(identity: UUID, request: Request):
    documents.delete(engine_for(request), identity)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500, pattern=r"^[^\x00]*$")]


@router.post("/{identity}/query")
async def query(identity: UUID, body: Question, request: Request):
    require_ai(request)
    result = await documents.answer(engine_for(request), request.app.state.ai_provider, identity, body.question)
    return reply(result)
