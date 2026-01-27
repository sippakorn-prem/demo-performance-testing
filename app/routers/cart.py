"""
Cart and checkout endpoints
"""
import asyncio
import random
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models import Product, CartItem, AppConfig

router = APIRouter(prefix="/cart", tags=["cart"])

# Global config (will be injected)
config: AppConfig = None


def set_config(cfg: AppConfig):
    """Set the global config"""
    global config
    config = cfg


def get_user_id(authorization: str = Header(None)) -> int:
    """Extract user ID from authorization header (simulated)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    # Simulate extracting user_id from token
    return random.randint(1, 1000)


class AddCartItemRequest(BaseModel):
    product_id: int
    quantity: int = 1


@router.post("/items")
async def add_cart_item(
    request: AddCartItemRequest,
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Add item to cart (requires authentication).
    TEACHING PURPOSE: Demonstrates authenticated endpoints.
    """
    try:
        # Apply artificial latency if configured
        if config and config.latency_checkout_ms > 0:
            await asyncio.sleep(config.latency_checkout_ms / 1000)
        
        # Verify product exists
        result = await db.execute(
            select(Product).where(Product.id == request.product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check if item already in cart
        result = await db.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == request.product_id
            )
        )
        existing_item = result.scalar_one_or_none()
        
        if existing_item:
            existing_item.quantity += request.quantity
        else:
            new_item = CartItem(
                user_id=user_id,
                product_id=request.product_id,
                quantity=request.quantity
            )
            db.add(new_item)
        
        await db.commit()
        
        return JSONResponse(
            status_code=200,
            content={"message": "Item added to cart", "product_id": request.product_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class CheckoutRequest(BaseModel):
    product_id: int
    quantity: int = 1


@router.post("/checkout")
async def checkout(
    request: CheckoutRequest,
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Checkout endpoint with stock management and concurrency issues.
    TEACHING PURPOSE: Demonstrates race conditions and 409 conflicts.
    """
    try:
        # Apply artificial latency if configured
        if config and config.latency_checkout_ms > 0:
            await asyncio.sleep(config.latency_checkout_ms / 1000)
        
        # Apply failure rate if configured
        if config and random.random() < config.failure_rate_checkout:
            raise HTTPException(status_code=502, detail="External payment service unavailable")
        
        # Get product with lock (simulate transaction)
        result = await db.execute(
            select(Product).where(Product.id == request.product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check stock (TEACHING PURPOSE: This is where race conditions occur)
        if product.stock < request.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock. Available: {product.stock}, Requested: {request.quantity}"
            )
        
        # Simulate payment processing delay
        await asyncio.sleep(0.1)
        
        # Update stock (TEACHING PURPOSE: Without proper locking, this causes race conditions)
        product.stock -= request.quantity
        await db.commit()
        
        return JSONResponse(
            status_code=200,
            content={
                "order_id": random.randint(10000, 99999),
                "product_id": request.product_id,
                "quantity": request.quantity,
                "status": "completed",
                "remaining_stock": product.stock
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
