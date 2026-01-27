"""
Heavy load endpoints for stress testing

TEACHING PURPOSE:
- Demonstrates different types of resource bottlenecks
- CPU-intensive operations
- Memory-intensive operations
- High latency operations
- Database-intensive operations
"""
import asyncio
import hashlib
import random
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.db import get_db
from app.models import Product, CartItem

router = APIRouter(prefix="/heavy", tags=["heavy"])


@router.get("/cpu")
async def cpu_intensive(
    iterations: int = Query(100000, ge=1, le=10000000, description="Number of hash iterations"),
    rounds: int = Query(10, ge=1, le=100, description="Number of hash rounds per iteration")
):
    """
    CPU-intensive endpoint - performs heavy hashing operations.
    
    TEACHING PURPOSE:
    - Demonstrates CPU bottlenecks
    - Shows how CPU usage affects response time
    - Useful for stress testing CPU capacity
    
    Parameters:
    - iterations: Number of hash operations (default: 100000)
    - rounds: Number of hash rounds per iteration (default: 10)
    """
    data = b"cpu_intensive_workload"
    result_hash = data
    
    # Perform CPU-intensive hashing
    for _ in range(iterations):
        for _ in range(rounds):
            result_hash = hashlib.sha256(result_hash).digest()
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "CPU-intensive operation completed",
            "iterations": iterations,
            "rounds": rounds,
            "hash": result_hash.hex()[:16] + "..."
        }
    )


@router.get("/memory")
async def memory_intensive(
    size_mb: int = Query(10, ge=1, le=500, description="Memory size in MB to allocate"),
    chunks: int = Query(10, ge=1, le=100, description="Number of memory chunks")
):
    """
    Memory-intensive endpoint - allocates large amounts of memory.
    
    TEACHING PURPOSE:
    - Demonstrates memory bottlenecks
    - Shows how memory allocation affects performance
    - Useful for stress testing memory capacity
    
    Parameters:
    - size_mb: Size of each chunk in MB (default: 10)
    - chunks: Number of chunks to allocate (default: 10)
    """
    # Allocate memory chunks
    memory_chunks = []
    bytes_per_chunk = size_mb * 1024 * 1024
    
    try:
        for i in range(chunks):
            # Create a large byte array filled with random data
            chunk = bytearray(bytes_per_chunk)
            # Fill with some pattern to ensure memory is actually allocated
            for j in range(0, len(chunk), 1024):
                chunk[j:j+8] = i.to_bytes(8, 'big')
            memory_chunks.append(chunk)
        
        # Perform some operations on the memory
        total_size = sum(len(chunk) for chunk in memory_chunks)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Memory-intensive operation completed",
                "chunks": chunks,
                "size_mb_per_chunk": size_mb,
                "total_size_mb": total_size / (1024 * 1024),
                "memory_allocated": True
            }
        )
    except MemoryError:
        raise HTTPException(
            status_code=507,
            detail=f"Insufficient memory to allocate {chunks} chunks of {size_mb}MB each"
        )


@router.get("/latency")
async def latency_intensive(
    delay_ms: int = Query(1000, ge=0, le=10000, description="Delay in milliseconds"),
    steps: int = Query(1, ge=1, le=10, description="Number of sequential delays")
):
    """
    Latency-intensive endpoint - introduces artificial delays.
    
    TEACHING PURPOSE:
    - Demonstrates latency bottlenecks
    - Shows how network/IO delays affect response time
    - Useful for stress testing under high latency conditions
    
    Parameters:
    - delay_ms: Delay per step in milliseconds (default: 1000)
    - steps: Number of sequential delays (default: 1)
    """
    total_delay = 0
    for step in range(steps):
        await asyncio.sleep(delay_ms / 1000.0)
        total_delay += delay_ms
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Latency-intensive operation completed",
            "delay_ms_per_step": delay_ms,
            "steps": steps,
            "total_delay_ms": total_delay
        }
    )


@router.get("/database")
async def database_intensive(
    complexity: int = Query(5, ge=1, le=20, description="Query complexity level"),
    joins: bool = Query(True, description="Include JOIN operations"),
    aggregations: bool = Query(True, description="Include aggregation operations"),
    db: AsyncSession = Depends(get_db)
):
    """
    Database-intensive endpoint - performs complex database queries.
    
    TEACHING PURPOSE:
    - Demonstrates database bottlenecks
    - Shows how complex queries affect performance
    - Useful for stress testing database capacity
    
    Parameters:
    - complexity: Number of operations to perform (default: 5)
    - joins: Whether to include JOIN operations (default: True)
    - aggregations: Whether to include aggregation operations (default: True)
    """
    results = []
    
    try:
        # Complex query 1: Count products with stock analysis
        if aggregations:
            result = await db.execute(
                select(
                    func.count(Product.id).label("total_products"),
                    func.avg(Product.price).label("avg_price"),
                    func.sum(Product.stock).label("total_stock"),
                    func.min(Product.stock).label("min_stock"),
                    func.max(Product.stock).label("max_stock")
                )
            )
            stats = result.first()
            results.append({
                "type": "aggregation",
                "total_products": stats.total_products,
                "avg_price": float(stats.avg_price) if stats.avg_price else 0,
                "total_stock": stats.total_stock,
                "min_stock": stats.min_stock,
                "max_stock": stats.max_stock
            })
        
        # Complex query 2: Products with cart items (JOIN)
        if joins:
            for i in range(complexity):
                result = await db.execute(
                    select(
                        Product.id,
                        Product.name,
                        Product.price,
                        Product.stock,
                        func.count(CartItem.id).label("cart_count")
                    )
                    .outerjoin(CartItem, Product.id == CartItem.product_id)
                    .group_by(Product.id, Product.name, Product.price, Product.stock)
                    .order_by(func.count(CartItem.id).desc())
                    .limit(100)
                )
                products = result.all()
                results.append({
                    "type": "join",
                    "iteration": i + 1,
                    "products_returned": len(products)
                })
        
        # Complex query 3: Subquery with filtering
        for i in range(complexity):
            # Find products that are in carts
            subquery = select(CartItem.product_id).distinct()
            result = await db.execute(
                select(Product)
                .where(Product.id.in_(subquery))
                .limit(50)
            )
            products = result.scalars().all()
            results.append({
                "type": "subquery",
                "iteration": i + 1,
                "products_in_carts": len(products)
            })
        
        # Complex query 4: Window functions (if supported)
        result = await db.execute(
            text("""
                SELECT 
                    id,
                    name,
                    price,
                    stock,
                    ROW_NUMBER() OVER (ORDER BY price DESC) as price_rank,
                    LAG(price, 1) OVER (ORDER BY price DESC) as prev_price
                FROM products
                LIMIT 100
            """)
        )
        ranked_products = result.fetchall()
        results.append({
            "type": "window_function",
            "products_ranked": len(ranked_products)
        })
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Database-intensive operation completed",
                "complexity": complexity,
                "joins": joins,
                "aggregations": aggregations,
                "queries_executed": len(results),
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )


@router.get("/mixed")
async def mixed_load(
    cpu_iterations: int = Query(50000, ge=1, le=1000000),
    memory_mb: int = Query(5, ge=1, le=100),
    delay_ms: int = Query(100, ge=0, le=1000),
    db_queries: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Mixed load endpoint - combines CPU, memory, latency, and database operations.
    
    TEACHING PURPOSE:
    - Demonstrates realistic mixed workloads
    - Shows how different resource types interact
    - Useful for comprehensive stress testing
    
    Parameters:
    - cpu_iterations: CPU hash iterations
    - memory_mb: Memory to allocate in MB
    - delay_ms: Artificial delay in milliseconds
    - db_queries: Number of database queries to execute
    """
    results = {}
    
    # CPU work
    data = b"mixed_workload"
    for _ in range(cpu_iterations):
        data = hashlib.sha256(data).digest()
    results["cpu"] = {"iterations": cpu_iterations, "completed": True}
    
    # Memory work
    memory_chunk = bytearray(memory_mb * 1024 * 1024)
    for i in range(0, len(memory_chunk), 1024):
        memory_chunk[i:i+8] = i.to_bytes(8, 'big')
    results["memory"] = {"size_mb": memory_mb, "allocated": True}
    
    # Latency
    await asyncio.sleep(delay_ms / 1000.0)
    results["latency"] = {"delay_ms": delay_ms, "completed": True}
    
    # Database work
    db_results = []
    for i in range(db_queries):
        result = await db.execute(
            select(func.count(Product.id))
        )
        count = result.scalar()
        db_results.append({"query": i + 1, "products_count": count})
    results["database"] = {"queries": db_queries, "results": db_results}
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Mixed load operation completed",
            "results": results
        }
    )
