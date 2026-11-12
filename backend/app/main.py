from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.health import router as health_router
from app.api.readiness import router as readiness_router
from app.api.imports import router as imports_router
from app.api.imports import error_response
from app.api.metadata import router as metadata_router
from app.api.audio import router as audio_router
from app.services.metadata import MetadataError
from app.config import Settings
from app.database import make_database_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    engine = make_database_engine(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            if engine is not None:
                engine.dispose()

    app = FastAPI(title="EchoBeats API", version="0.1.0", lifespan=lifespan)
    app.state.database_engine = engine
    app.state.settings = config
    app.include_router(health_router, prefix="/api/v1", tags=["Estado"])
    app.include_router(readiness_router, prefix="/api/v1", tags=["Estado"])
    app.include_router(imports_router, prefix="/api/v1", tags=["Importación"])
    app.include_router(metadata_router, prefix="/api/v1", tags=["Metadatos"])
    app.include_router(audio_router, prefix="/api/v1", tags=["Audio"])

    @app.exception_handler(MetadataError)
    async def metadata_error(request, exc):
        return error_response(exc.code, exc.message, exc.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_data(request, exc):
        return error_response("invalid_data", "Revisa los campos enviados; hay datos vacíos, no válidos o no permitidos.", 422)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return error_response("database_unavailable", "No se pudo completar la operación con la base de datos.", 503)

    @app.middleware("http")
    async def validate_write_origin(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            # Clientes locales sin Origin (terminal) se admiten. Navegadores
            # con Origin explícito deben coincidir con el origen configurado.
            if origin is not None and origin not in config.origins():
                return JSONResponse(
                    status_code=403,
                    content={"error": {"code": "origin_not_allowed", "message": "Origen no permitido."}},
                )
        return await call_next(request)

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.hosts(), www_redirect=False)
    return app


app = create_app()
