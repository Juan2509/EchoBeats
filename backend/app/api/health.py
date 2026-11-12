from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Confirma el proceso; la disponibilidad de BD se añadirá en P04."""
    return HealthResponse(status="ok")
