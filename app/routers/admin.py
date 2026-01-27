"""
Admin endpoints for workshop configuration
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.models import AppConfig

router = APIRouter(prefix="/admin", tags=["admin"])

# Global config (will be injected)
config: AppConfig = None


def set_config(cfg: AppConfig):
    """Set the global config"""
    global config
    config = cfg


class LatencyConfig(BaseModel):
    """Configure artificial latency per endpoint group"""
    auth: float = Field(0, ge=0, description="Latency for auth endpoints (ms)")
    products: float = Field(0, ge=0, description="Latency for product endpoints (ms)")
    checkout: float = Field(0, ge=0, description="Latency for checkout endpoints (ms)")


class FailureConfig(BaseModel):
    """Configure failure rate per endpoint group"""
    auth: float = Field(0, ge=0, le=1, description="Failure rate for auth endpoints (0.0-1.0)")
    products: float = Field(0, ge=0, le=1, description="Failure rate for product endpoints (0.0-1.0)")
    checkout: float = Field(0, ge=0, le=1, description="Failure rate for checkout endpoints (0.0-1.0)")


class CacheConfig(BaseModel):
    """Configure cache settings"""
    enabled: bool = Field(True, description="Enable/disable cache")
    hit_ratio: float = Field(0.7, ge=0, le=1, description="Cache hit ratio (0.0-1.0)")


@router.post("/latency")
async def set_latency(latency: LatencyConfig):
    """
    Set artificial latency for endpoint groups.
    TEACHING PURPOSE: Allows instructor to introduce latency bottlenecks during workshop.
    """
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not initialized")
    await config.update(
        latency_auth_ms=latency.auth,
        latency_products_ms=latency.products,
        latency_checkout_ms=latency.checkout
    )
    return JSONResponse(
        status_code=200,
        content={
            "message": "Latency configuration updated",
            "config": {
                "auth_ms": config.latency_auth_ms,
                "products_ms": config.latency_products_ms,
                "checkout_ms": config.latency_checkout_ms
            }
        }
    )


@router.post("/failure")
async def set_failure(failure: FailureConfig):
    """
    Set failure rate for endpoint groups.
    TEACHING PURPOSE: Allows instructor to introduce errors during workshop.
    """
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not initialized")
    await config.update(
        failure_rate_auth=failure.auth,
        failure_rate_products=failure.products,
        failure_rate_checkout=failure.checkout
    )
    return JSONResponse(
        status_code=200,
        content={
            "message": "Failure rate configuration updated",
            "config": {
                "auth": config.failure_rate_auth,
                "products": config.failure_rate_products,
                "checkout": config.failure_rate_checkout
            }
        }
    )


@router.post("/cache")
async def set_cache(cache: CacheConfig):
    """
    Configure cache settings.
    TEACHING PURPOSE: Demonstrates cache impact on performance.
    """
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not initialized")
    await config.update(
        cache_enabled=cache.enabled,
        cache_hit_ratio=cache.hit_ratio
    )
    return JSONResponse(
        status_code=200,
        content={
            "message": "Cache configuration updated",
            "config": {
                "enabled": config.cache_enabled,
                "hit_ratio": config.cache_hit_ratio
            }
        }
    )


class ConfigUpdate(BaseModel):
    """Update any configuration value"""
    auth_hashing_rounds: Optional[int] = Field(None, ge=1, description="CPU hashing rounds for login")
    latency_auth_ms: Optional[float] = Field(None, ge=0)
    latency_products_ms: Optional[float] = Field(None, ge=0)
    latency_checkout_ms: Optional[float] = Field(None, ge=0)
    failure_rate_auth: Optional[float] = Field(None, ge=0, le=1)
    failure_rate_products: Optional[float] = Field(None, ge=0, le=1)
    failure_rate_checkout: Optional[float] = Field(None, ge=0, le=1)
    cache_enabled: Optional[bool] = None
    cache_hit_ratio: Optional[float] = Field(None, ge=0, le=1)


@router.post("/config")
async def update_config(update: ConfigUpdate):
    """
    Update any configuration value.
    TEACHING PURPOSE: Allows instructor to modify system behavior during workshop.
    """
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not initialized")
    update_dict = update.dict(exclude_none=True)
    await config.update(**update_dict)
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Configuration updated",
            "config": {
                "auth_hashing_rounds": config.auth_hashing_rounds,
                "latency": {
                    "auth_ms": config.latency_auth_ms,
                    "products_ms": config.latency_products_ms,
                    "checkout_ms": config.latency_checkout_ms
                },
                "failure_rate": {
                    "auth": config.failure_rate_auth,
                    "products": config.failure_rate_products,
                    "checkout": config.failure_rate_checkout
                },
                "cache": {
                    "enabled": config.cache_enabled,
                    "hit_ratio": config.cache_hit_ratio
                }
            }
        }
    )


@router.get("/config")
async def get_config():
    """Get current configuration"""
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not initialized")
    return JSONResponse(
        status_code=200,
        content={
            "auth_hashing_rounds": config.auth_hashing_rounds,
            "latency": {
                "auth_ms": config.latency_auth_ms,
                "products_ms": config.latency_products_ms,
                "checkout_ms": config.latency_checkout_ms
            },
            "failure_rate": {
                "auth": config.failure_rate_auth,
                "products": config.failure_rate_products,
                "checkout": config.failure_rate_checkout
            },
            "cache": {
                "enabled": config.cache_enabled,
                "hit_ratio": config.cache_hit_ratio
            }
        }
    )
