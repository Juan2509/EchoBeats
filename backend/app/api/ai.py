import os
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, SecretStr, StringConstraints

from app.api.imports import error_response
from app.integrations.ai import status

router = APIRouter()


class OpenAIKeyInput(BaseModel):
    key: Annotated[str, StringConstraints(strip_whitespace=True, max_length=512, pattern=r'^sk-[A-Za-z0-9_-]+$')]


def key_path(settings):
    return settings.media_root.parent / '.openai-key'


def load_saved_key(settings):
    if settings.ai_key_editable:
        try:
            settings.openai_api_key = SecretStr(key_path(settings).read_text(encoding='ascii').strip())
        except FileNotFoundError:
            pass


@router.get('/ai/status')
def configuration(request: Request):
    settings = request.app.state.settings
    return JSONResponse(
        {**status(settings), 'key_editable': settings.ai_key_editable},
        headers={'Cache-Control': 'no-store'},
    )


@router.put('/ai/key')
def save_key(request: Request, body: OpenAIKeyInput):
    settings = request.app.state.settings
    if not settings.ai_key_editable or not settings.ai_enabled or request.headers.get('origin') not in settings.origins():
        return error_response('ai_key_write_forbidden', 'No se puede guardar la clave desde este origen.', 403)

    path = key_path(settings)
    with request.app.state.ai_key_lock:
        temporary = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(mode='w', encoding='ascii', dir=path.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(body.key)
            os.replace(temporary, path)
        except OSError:
            return error_response('ai_key_save_failed', 'No se pudo guardar la clave en el servidor.', 503)
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
        settings.openai_api_key = SecretStr(body.key)
    return configuration(request)
