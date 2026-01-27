"""
Health and metrics endpoints
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )
