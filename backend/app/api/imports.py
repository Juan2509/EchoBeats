from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException
from starlette.requests import Request as FormRequest
from python_multipart.exceptions import MultipartParseError

from app.integrations.storage import MediaStore
from app.services.imports import import_file
from app.services.metadata import enrich_track, MetadataError
from sqlalchemy.exc import SQLAlchemyError
from mutagen import MutagenError
from uuid import UUID

router = APIRouter()


def error_response(code, message, status):
    return JSONResponse(status_code=status, content={
        "error": {"code": code, "message": message, "fields": [], "request_id": str(uuid4())},
    })


@router.post("/imports", openapi_extra={
    "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {
        "type": "object", "required": ["files"], "properties": {
            "files": {"type": "array", "minItems": 1, "maxItems": 20, "items": {"type": "string", "format": "binary"}},
        },
    }}}},
})
async def import_audio(request: Request):
    config = request.app.state.settings
    engine = request.app.state.database_engine
    if engine is None:
        return error_response("database_unavailable", "La base de datos no está configurada.", 503)
    if request.headers.get("content-type", "").split(";", 1)[0].lower() != "multipart/form-data":
        return error_response("invalid_multipart", "Envía los archivos como formulario multipart.", 415)
    # Contar bytes recibidos, sin confiar únicamente en Content-Length.
    consumed = 0

    async def receive_limited():
        nonlocal consumed
        message = await request.receive()
        consumed += len(message.get("body", b""))
        if consumed > config.import_max_request_bytes:
            # El parser cierra sus temporales al recibir MultiPartException.
            raise MultiPartException("import_body_too_large")
        return message

    form_request = FormRequest(request.scope, receive=receive_limited)
    try:
        async with form_request.form(max_files=config.import_max_files, max_fields=0) as form:
            parts = form.multi_items()
            if not parts or any(key != "files" or not isinstance(value, UploadFile) for key, value in parts):
                return error_response("invalid_files", "Selecciona uno o varios archivos en el campo files.", 422)
            store = MediaStore(config.media_root)
            results = []
            for index, (_, upload) in enumerate(parts):
                result = await run_in_threadpool(
                    import_file, engine, store, upload.file, upload.filename, config.import_max_file_bytes,
                )
                if result["status"] in {"imported", "duplicate"}:
                    try:
                        _, _, warnings = await run_in_threadpool(enrich_track, engine, store, UUID(result["track_id"]))
                        if warnings:
                            result["metadata_warnings"] = warnings
                    except (MetadataError, MutagenError, OSError, ValueError, SQLAlchemyError):
                        # El original ya está confirmado: no convertirlo en rechazo.
                        result["metadata_warnings"] = ["metadata_pending"]
                results.append({"index": index, **result})
            return {"results": results}
    except HTTPException as exc:
        if exc.detail == "import_body_too_large":
            return error_response("request_too_large", "La solicitud supera el tamaño total permitido.", 413)
        return error_response("invalid_multipart", "Formulario no válido o demasiados archivos/campos.", 422)
    except (MultiPartException, MultipartParseError):
        return error_response("invalid_multipart", "No se pudo leer el formulario multipart.", 422)
