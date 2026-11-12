from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.database import database_readiness

router = APIRouter()


@router.get("/ready")
def ready(request: Request):
    checks = database_readiness(request.app.state.database_engine)
    available = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if available else 503,
        content={"status": "ready" if available else "not_ready", "checks": checks},
    )
