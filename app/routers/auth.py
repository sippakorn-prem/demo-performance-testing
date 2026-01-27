"""
Authentication endpoints (simulated)
"""
import asyncio
import hashlib
import random
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.models import AppConfig

router = APIRouter(prefix="/auth", tags=["auth"])

# Global config (will be injected)
config: AppConfig = None


def set_config(cfg: AppConfig):
    """Set the global config"""
    global config
    config = cfg


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(request: LoginRequest):
    """
    Simulated login endpoint with configurable CPU-intensive hashing.
    TEACHING PURPOSE: Demonstrates CPU bottlenecks.
    """
    # Simulate DB read delay
    await asyncio.sleep(0.05)
    
    # CPU-intensive hashing (configurable via admin endpoint)
    data = request.password.encode()
    hashing_rounds = config.auth_hashing_rounds if config else 10000
    for _ in range(hashing_rounds):
        data = hashlib.sha256(data).digest()
    
    # Simulate additional DB write delay
    await asyncio.sleep(0.05)
    
    return JSONResponse(
        status_code=200,
        content={
            "access_token": f"fake_jwt_token_{random.randint(1000, 9999)}",
            "token_type": "bearer",
            "user_id": random.randint(1, 1000)
        }
    )
