"""Audio original por ID de pista; ningún cliente proporciona rutas de disco."""

import os
import stat
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy import select

from app.api.metadata import engine_for
from app.integrations.storage import MediaStore
from app.integrations.audio_formats import AUDIO_MIME_TYPES, stored_audio_type
from app.models.catalog import media_asset, track
from app.services.metadata import MetadataError

router = APIRouter()


@router.head('/tracks/{track_id}/audio', response_class=Response,
             summary='Cabeceras de audio sin transferir el archivo')
@router.get('/tracks/{track_id}/audio', response_class=FileResponse,
                  responses={200: {'content': {mime: {} for mime in set(AUDIO_MIME_TYPES.values())}},
                             206: {'description': 'Bytes solicitados; Content-Range indica posición y tamaño.'},
                             400: {'description': 'Cabecera Range mal formada.'},
                             404: {'description': 'Pista o archivo no disponible.'},
                             416: {'description': 'Rango fuera del archivo; Content-Range: bytes */tamaño.'},
                             503: {'description': 'Almacenamiento o base de datos inaccesible.'}})
def get_audio(track_id: UUID, request: Request):
    with engine_for(request).connect() as connection:
        resource = connection.execute(
            select(media_asset).join(track, track.c.audio_asset_id == media_asset.c.id)
            .where(track.c.id == track_id),
        ).first()
        if resource is None:
            raise MetadataError('track_not_found', 'No existe esa canción.', 404)
    if resource.kind != 'audio' or resource.mime_type != stored_audio_type(resource.storage_key):
        raise MetadataError('media_missing', 'El audio de esta canción no está disponible.', 404)
    try:
        path = MediaStore(request.app.state.settings.media_root).path_for(resource.storage_key)
        if not stat.S_ISREG(path.stat().st_mode):
            raise MetadataError('media_missing', 'El audio de esta canción no está disponible.', 404)
        # Abrir antes de emitir cabeceras: detecta permisos, directorios y pérdida
        # del archivo sin devolver excepciones que revelen rutas internas.
        with path.open('rb') as stream:
            info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size != resource.byte_size:
            raise MetadataError('media_missing', 'El audio de esta canción no está disponible.', 404)
    except (ValueError, FileNotFoundError, NotADirectoryError, IsADirectoryError):
        raise MetadataError('media_missing', 'No se encuentra el audio de esta canción.', 404) from None
    except OSError:
        raise MetadataError('media_unavailable', 'No se pudo acceder al audio. Vuelve a intentarlo más tarde.', 503) from None
    response = FileResponse(path, media_type=resource.mime_type, stat_result=info, headers={
        'Content-Disposition': 'inline', 'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'private, no-cache',
    })
    # Range solo modifica GET; HEAD describe siempre el recurso completo.
    if request.method == 'HEAD':
        return Response(headers=dict(response.headers))
    return response
