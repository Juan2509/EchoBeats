from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.health import router as health_router
from app.api.readiness import router as readiness_router
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
    app.include_router(health_router, prefix="/api/v1", tags=["Estado"])
    app.include_router(readiness_router, prefix="/api/v1", tags=["Estado"])

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
