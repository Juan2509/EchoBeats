from typing import Annotated
from uuid import UUID
from urllib.parse import urlencode

from fastapi import APIRouter, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException
from starlette.requests import Request as FormRequest
from python_multipart.exceptions import MultipartParseError

from app.integrations.storage import MediaStore
from app.integrations.tags import normalized, prepare_cover
from app.models.catalog import media_asset
from app.services import metadata as service
from app.services import library
from app.services.covers import publications, save_cover

router = APIRouter()
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Names = Annotated[list[Name], Field(max_length=20)]
SearchText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200, pattern=r'^[^\x00]*$')]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_values(self):
        for key in self.model_fields_set:
            value = getattr(self, key)
            if value is None and key not in {"track_number", "cover_asset_id"}:
                raise ValueError("Este campo no admite null.")
            strings = value if isinstance(value, list) else [value] if isinstance(value, str) else []
            for name in strings:
                if "\x00" in name or len(normalized(name)) > 320:
                    raise ValueError("Texto no válido.")
                name.encode("utf-8")
            if isinstance(value, list) and len({normalized(name) for name in value}) != len(value):
                raise ValueError("Los artistas no deben repetirse.")
        return self


class TrackPatch(InputModel):
    title: Name | None = None
    artist_names: Names | None = None
    album_id: UUID | None = None
    track_number: Annotated[int, Field(strict=True, ge=1, le=2_147_483_647)] | None = None
    cover_asset_id: UUID | None = None


class AlbumCreate(InputModel):
    title: Name
    artist_names: Names = Field(default_factory=list)


class AlbumPatch(InputModel):
    title: Name | None = None
    artist_names: Names | None = None
    cover_asset_id: UUID | None = None


def engine_for(request):
    engine = request.app.state.database_engine
    if engine is None:
        raise service.MetadataError("database_unavailable", "La base de datos no está configurada.", 503)
    return engine


def response(result, status=200):
    data, token = result
    return JSONResponse(status_code=status, content=jsonable_encoder(data), headers={"ETag": token, "Cache-Control": "no-store"})


@router.get("/tracks/{track_id}")
def get_track(track_id: UUID, request: Request):
    with engine_for(request).connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        with connection.begin():
            return response(service.track_data(connection, track_id))


@router.get("/tracks")
def list_tracks(request: Request, limit: int = Query(24, ge=1, le=100), offset: int = Query(0, ge=0), album_id: UUID | None = None, q: SearchText = ''):
    q = q.strip()
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        return library.page(connection, 'tracks', limit, offset, q, album_id)


@router.patch("/tracks/{track_id}")
def patch_track(track_id: UUID, changes: TrackPatch, request: Request, if_match: str | None = Header(None)):
    return response(service.patch_track(engine_for(request), track_id, changes.model_dump(exclude_unset=True), if_match))


@router.post("/tracks/{track_id}/extract-metadata")
def extract_metadata(track_id: UUID, request: Request, if_match: str | None = Header(None)):
    if if_match is None:
        raise service.MetadataError("revision_required", "Recarga la canción antes de volver a leer sus etiquetas.", 428)
    data, token, warnings = service.enrich_track(engine_for(request), MediaStore(request.app.state.settings.media_root), track_id, if_match)
    return response(({**data, "metadata_warnings": warnings}, token))


@router.get("/albums")
def list_albums(request: Request, limit: int = Query(24, ge=1, le=100), offset: int = Query(0, ge=0), q: SearchText = '', include_empty_system: bool = True):
    q = q.strip()
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        return library.page(connection, 'albums', limit, offset, q, include_empty_system=include_empty_system)


@router.get('/library/search')
def search_library(request: Request, q: SearchText = Query(..., min_length=1)):
    q = q.strip()
    if not q:
        raise service.MetadataError('invalid_query', 'Escribe un texto para buscar.')
    with engine_for(request).connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        groups = {kind: library.page(connection, kind, 10, 0, q) for kind in ('tracks', 'albums', 'playlists')}
    for kind, view in [('tracks', 'canciones'), ('albums', 'albumes')]:
        groups[kind]['href'] = '/biblioteca?' + urlencode({'vista': view, 'q': q})
    groups['playlists']['href'] = None  # navegación y gestión se incorporan en P11
    return {'query': q, **groups}


@router.get("/albums/{album_id}")
def get_album(album_id: UUID, request: Request):
    with engine_for(request).connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        with connection.begin():
            return response(service.album_data(connection, album_id))


@router.post("/albums")
def create_album(body: AlbumCreate, request: Request):
    return response(service.create_album(engine_for(request), body.title, body.artist_names), 201)


@router.patch("/albums/{album_id}")
def patch_album(album_id: UUID, changes: AlbumPatch, request: Request, if_match: str | None = Header(None)):
    return response(service.patch_album(engine_for(request), album_id, changes.model_dump(exclude_unset=True), if_match))


@router.get("/assets/{asset_id}/content")
def cover_content(asset_id: UUID, request: Request):
    with engine_for(request).connect() as connection:
        resource = connection.execute(select(media_asset).where(media_asset.c.id == asset_id)).first()
    if resource is None or resource.kind not in {"cover", "image"} or resource.mime_type not in {"image/png", "image/jpeg"}:
        raise service.MetadataError("cover_not_found", "No existe esa portada.", 404)
    try:
        path = MediaStore(request.app.state.settings.media_root).path_for(resource.storage_key)
    except ValueError:
        raise service.MetadataError("media_missing", "No se encuentra la imagen.", 404) from None
    if not path.is_file():
        raise service.MetadataError("media_missing", "No se encuentra la imagen.", 404)
    return FileResponse(path, media_type=resource.mime_type, content_disposition_type="inline", headers={
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=3600",
    })


def upload_cover(engine, store, stream):
    try:
        cover = prepare_cover(stream.read(5 * 1024 * 1024 + 1))
    except ValueError as exc:
        raise service.MetadataError("invalid_cover", str(exc)) from None
    with publications(engine, store) as created:
        with engine.begin() as connection:
            asset_id = save_cover(connection, store, cover, created)
    return {"id": asset_id, "mime_type": "image/png", "width_px": cover.width, "height_px": cover.height,
            "content_url": f"/api/v1/assets/{asset_id}/content"}


@router.post("/assets", status_code=201, openapi_extra={
    "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {
        "type": "object", "required": ["file", "purpose"], "properties": {
            "file": {"type": "string", "format": "binary"}, "purpose": {"type": "string", "enum": ["cover"]},
        },
    }}}},
})
async def post_cover(request: Request):
    engine = engine_for(request)
    received = 0

    async def limited_receive():
        nonlocal received
        message = await request.receive()
        received += len(message.get("body", b""))
        if received > 6 * 1024 * 1024:
            raise MultiPartException("cover_body_too_large")
        return message

    if request.headers.get("content-type", "").split(";", 1)[0].lower() != "multipart/form-data":
        raise service.MetadataError("invalid_multipart", "Envía una portada PNG o JPEG como formulario multipart.", 415)
    try:
        async with FormRequest(request.scope, receive=limited_receive).form(max_files=1, max_fields=1) as form:
            parts = form.multi_items()
            if len(parts) != 2 or set(key for key, _ in parts) != {"file", "purpose"} or form.get("purpose") != "cover" or not isinstance(form.get("file"), UploadFile):
                raise service.MetadataError("invalid_cover", "Envía un archivo file y purpose=cover.")
            return await run_in_threadpool(upload_cover, engine, MediaStore(request.app.state.settings.media_root), form["file"].file)
    except HTTPException as exc:
        if exc.detail == "cover_body_too_large":
            raise service.MetadataError("request_too_large", "La solicitud de portada supera el límite permitido.", 413) from None
        raise service.MetadataError("invalid_multipart", "El formulario de portada no es válido.") from None
    except (MultiPartException, MultipartParseError):
        raise service.MetadataError("invalid_multipart", "No se pudo leer el formulario de portada.") from None
