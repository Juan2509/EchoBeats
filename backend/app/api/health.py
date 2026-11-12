from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Confirma el proceso; /ready comprueba las dependencias de base de datos."""
    return HealthResponse(status="ok")
