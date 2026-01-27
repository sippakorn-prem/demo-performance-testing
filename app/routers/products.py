"""
Product endpoints with pagination and caching
"""
import asyncio
import random
from typing import Optional
from fastapi import APIRouter, Query, Path, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import get_db
from app.models import Product, AppConfig

router = APIRouter(prefix="/products", tags=["products"])

# Global config (will be injected)
config: AppConfig = None

# Simple in-memory cache (TEACHING PURPOSE: demonstrates cache hit ratio)
_cache: dict = {}


def set_config(cfg: AppConfig):
    """Set the global config"""
    global config
    config = cfg


def _get_cache_key(product_id: int) -> str:
    """Generate cache key"""
    return f"product:{product_id}"


@router.get("")
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List products with pagination.
    TEACHING PURPOSE: Demonstrates database query patterns.
    """
    # Apply artificial latency if configured
    if config and config.latency_products_ms > 0:
        await asyncio.sleep(config.latency_products_ms / 1000)
    
    # Apply failure rate if configured
    if config and random.random() < config.failure_rate_products:
        raise HTTPException(status_code=500, detail="Simulated product service failure")
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Query database
    result = await db.execute(
        select(Product)
        .offset(offset)
        .limit(limit)
    )
    products = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(select(func.count(Product.id)))
    total = count_result.scalar()
    
    return JSONResponse(
        status_code=200,
        content={
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "stock": p.stock
                }
                for p in products
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )


@router.get("/{product_id}")
async def get_product(
    product_id: int = Path(..., description="Product ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get product detail with optional caching.
    TEACHING PURPOSE: Demonstrates cache hit ratio impact.
    """
    # Apply artificial latency if configured
    if config and config.latency_products_ms > 0:
        await asyncio.sleep(config.latency_products_ms / 1000)
    
    # Apply failure rate if configured
    if config and random.random() < config.failure_rate_products:
        raise HTTPException(status_code=500, detail="Simulated product service failure")
    
    # Check cache if enabled
    cache_key = _get_cache_key(product_id)
    if config and config.cache_enabled and cache_key in _cache:
        # Simulate cache hit ratio
        if random.random() < config.cache_hit_ratio:
            return JSONResponse(
                status_code=200,
                content=_cache[cache_key]
            )
    
    # Query database
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "description": product.description or f"Description for {product.name}"
    }
    
    # Update cache if enabled
    if config and config.cache_enabled:
        _cache[cache_key] = product_data
    
    return JSONResponse(status_code=200, content=product_data)
