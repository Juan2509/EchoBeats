from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.integrations.ai import status

router = APIRouter()


@router.get('/ai/status')
def configuration(request: Request):
    return JSONResponse(status(request.app.state.settings), headers={'Cache-Control': 'no-store'})
