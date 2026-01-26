"""
FastAPI Demo API for Performance Testing Workshop

This API is intentionally designed to demonstrate performance issues under load.
It includes artificial latencies, connection pool limits, CPU-intensive tasks,
and configurable failure rates to teach performance testing concepts.

TEACHING PURPOSE: Show real-world bottlenecks in a controlled, observable way.
"""

import asyncio
import hashlib
import random
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator

# ============================================================================
# CONFIGURATION STATE (Teaching: Simulates runtime config changes)
# ============================================================================

class AppConfig:
    """Runtime configuration that can be updated during the workshop."""
    
    def __init__(self):
        # Connection pool settings (Teaching: Simulates DB connection pool)
        self.poolEnabled: bool = True
        self.poolMax: int = 30  # Default: stable but can be reduced to show bottleneck
        self.poolWaitTimeoutMs: int = 300  # 300ms timeout
        
        # CPU burn settings (Teaching: Simulates expensive computation)
        self.loginCpuRounds: int = 10000  # Default: moderate CPU usage
        self.cpuStressRounds: int = 50000  # Default: heavy CPU stress for /stress/cpu endpoint
        
        # Memory stress settings (Teaching: Simulates memory-intensive operations)
        self.memoryStressMb: int = 50  # Default: 50MB memory allocation for /stress/memory endpoint
        
        # Failure rate settings (Teaching: Simulates external dependency failures)
        self.checkoutFailRate: float = 0.02  # 2% failure rate
        
        # Lock for thread-safe config updates
        self._lock = asyncio.Lock()
    
    async def update(self, **kwargs):
        """Thread-safe config update."""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

# Global config instance
config = AppConfig()

# ============================================================================
# CONNECTION POOL SIMULATOR (Teaching: Shows resource exhaustion)
# ============================================================================

class ConnectionPool:
    """
    Fake connection pool limiter.
    
    TEACHING PURPOSE: Demonstrates how connection pool limits cause 503 errors
    when too many concurrent requests exceed available connections.
    """
    
    def __init__(self):
        self.in_use: int = 0
        self._lock = asyncio.Lock()
    
    @asynccontextmanager
    async def acquire(self, timeout_ms: int):
        """
        Acquire a connection from the pool.
        
        Returns:
            Context manager that releases connection on exit.
        
        Raises:
            HTTPException(503): If pool is full and timeout exceeded.
        """
        start_time = time.time()
        
        # Wait for available connection
        while True:
            async with self._lock:
                if self.in_use < config.poolMax:
                    self.in_use += 1
                    break
            
            # Check timeout
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms >= timeout_ms:
                raise HTTPException(
                    status_code=503,
                    detail=f"Connection pool exhausted. Timeout after {timeout_ms}ms"
                )
            
            # Brief wait before retry (Teaching: Simulates connection wait)
            await asyncio.sleep(0.01)
        
        try:
            yield
        finally:
            async with self._lock:
                self.in_use -= 1
    
    def get_status(self) -> dict:
        """Get current pool status for monitoring."""
        return {
            "inUse": self.in_use,
            "max": config.poolMax,
            "available": config.poolMax - self.in_use,
            "enabled": config.poolEnabled
        }

# Global pool instance
pool = ConnectionPool()

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="Performance Testing Demo API",
    description="Demo API for Locust performance testing workshop",
    version="1.0.0"
)

# ============================================================================
# PROMETHEUS METRICS INSTRUMENTATION
# ============================================================================

# TEACHING PURPOSE: Expose Prometheus metrics at /metrics endpoint
# This allows Grafana to visualize request rates, latencies, and error rates
Instrumentator().instrument(app).expose(app)

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health():
    """
    Health check endpoint - fast response with pool status.
    
    TEACHING PURPOSE: Shows baseline performance and pool monitoring.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "pool": pool.get_status(),
            "config": {
                "loginCpuRounds": config.loginCpuRounds,
                "cpuStressRounds": config.cpuStressRounds,
                "memoryStressMb": config.memoryStressMb,
                "checkoutFailRate": config.checkoutFailRate
            }
        }
    )


@app.get("/products")
async def get_products():
    """
    List products endpoint - adds variable latency.
    
    TEACHING PURPOSE: Demonstrates how latency affects p95 metrics.
    Simulates database query with 100-300ms delay.
    """
    # Teaching: Variable latency simulates real-world DB query times
    latency_ms = random.uniform(100, 300)
    await asyncio.sleep(latency_ms / 1000)
    
    return JSONResponse(
        status_code=200,
        content={
            "products": [
                {"id": 1, "name": "Product 1", "price": 19.99},
                {"id": 2, "name": "Product 2", "price": 29.99},
                {"id": 3, "name": "Product 3", "price": 39.99},
            ]
        }
    )


@app.get("/products/{product_id}")
async def get_product(product_id: int = Path(..., description="Product ID")):
    """
    Get product detail - uses connection pool limiter.
    
    TEACHING PURPOSE: Shows how connection pool limits cause 503 errors
    when concurrent requests exceed poolMax.
    """
    if not config.poolEnabled:
        # Teaching: Bypass pool when disabled (for comparison)
        await asyncio.sleep(0.1)
        return JSONResponse(
            status_code=200,
            content={"id": product_id, "name": f"Product {product_id}", "price": 19.99}
        )
    
    # Teaching: Acquire connection from pool (may timeout if pool is full)
    try:
        async with pool.acquire(config.poolWaitTimeoutMs):
            # Simulate DB query time
            await asyncio.sleep(0.1)
            return JSONResponse(
                status_code=200,
                content={"id": product_id, "name": f"Product {product_id}", "price": 19.99}
            )
    except HTTPException:
        # Re-raise 503 from pool timeout
        raise


@app.post("/login")
async def login():
    """
    Login endpoint - CPU-intensive task.
    
    TEACHING PURPOSE: Demonstrates CPU bottlenecks.
    Uses repeated SHA256 hashing to simulate expensive computation.
    """
    # Teaching: CPU burn simulates password hashing, encryption, etc.
    data = b"password123"
    for _ in range(config.loginCpuRounds):
        data = hashlib.sha256(data).digest()
    
    return JSONResponse(
        status_code=200,
        content={"token": "fake_jwt_token", "userId": 123}
    )


@app.post("/checkout")
async def checkout():
    """
    Checkout endpoint - uses pool + random failures.
    
    TEACHING PURPOSE: Shows error rate monitoring and connection pool limits.
    """
    # Teaching: Random failures simulate external dependency issues
    if random.random() < config.checkoutFailRate:
        raise HTTPException(
            status_code=502,
            detail="External payment service unavailable"
        )
    
    if not config.poolEnabled:
        await asyncio.sleep(0.15)
        return JSONResponse(
            status_code=200,
            content={"orderId": random.randint(1000, 9999), "status": "completed"}
        )
    
    # Teaching: Uses connection pool (may timeout)
    try:
        async with pool.acquire(config.poolWaitTimeoutMs):
            # Simulate checkout processing
            await asyncio.sleep(0.15)
            return JSONResponse(
                status_code=200,
                content={"orderId": random.randint(1000, 9999), "status": "completed"}
            )
    except HTTPException:
        raise


@app.get("/heavy")
async def heavy():
    """
    Heavy endpoint - high latency (800-1200ms).
    
    TEACHING PURPOSE: Demonstrates slow endpoints that affect p95 metrics.
    Simulates complex report generation or data aggregation.
    """
    # Teaching: High latency shows impact on overall system performance
    latency_ms = random.uniform(800, 1200)
    await asyncio.sleep(latency_ms / 1000)
    
    return JSONResponse(
        status_code=200,
        content={"data": "heavy computation result", "processed": 10000}
    )


@app.post("/stress/cpu")
async def stress_cpu():
    """
    CPU stress test endpoint - configurable CPU-intensive task.
    
    TEACHING PURPOSE: Demonstrates CPU bottlenecks and how they affect
    system performance. Watch CPU usage spike in Grafana when this is called.
    
    Configurable via: config.cpuStressRounds (default: 50000)
    Higher values = more CPU usage = longer response time
    """
    # Teaching: CPU burn simulates expensive computation (image processing, encryption, etc.)
    data = b"cpu_stress_test_data"
    for _ in range(config.cpuStressRounds):
        data = hashlib.sha256(data).digest()
        # Add some additional computation to increase CPU load
        _ = sum(range(100))
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "CPU stress test completed",
            "rounds": config.cpuStressRounds,
            "result": data.hex()[:16]  # Return first 16 chars of hash
        }
    )


@app.post("/stress/memory")
async def stress_memory():
    """
    Memory stress test endpoint - allocates and holds memory.
    
    TEACHING PURPOSE: Demonstrates memory usage and potential memory leaks.
    Watch memory usage increase in Grafana when this is called repeatedly.
    
    Configurable via: config.memoryStressMb (default: 50MB)
    Higher values = more memory allocated per request
    """
    # Teaching: Memory allocation simulates data processing, caching, etc.
    # Allocate memory in chunks to simulate real-world memory usage patterns
    memory_chunks = []
    bytes_per_mb = 1024 * 1024
    chunk_size = 1024 * 100  # 100KB chunks
    
    try:
        for _ in range(0, config.memoryStressMb * bytes_per_mb, chunk_size):
            # Allocate chunk of memory filled with data
            chunk = bytearray(random.getrandbits(8) for _ in range(chunk_size))
            memory_chunks.append(chunk)
        
        # Hold the memory for a short time to simulate processing
        await asyncio.sleep(0.1)
        
        # Calculate some result to make it look like we're using the memory
        total_size = sum(len(chunk) for chunk in memory_chunks)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Memory stress test completed",
                "allocated_mb": config.memoryStressMb,
                "total_bytes": total_size,
                "chunks": len(memory_chunks)
            }
        )
    finally:
        # Explicitly clear memory (though Python GC will handle it)
        memory_chunks.clear()
        del memory_chunks


@app.post("/stress/both")
async def stress_both():
    """
    Combined CPU and Memory stress test endpoint.
    
    TEACHING PURPOSE: Demonstrates simultaneous CPU and memory bottlenecks.
    Perfect for showing how both resources can be stressed at once.
    """
    # Teaching: Real-world scenarios often stress both CPU and memory
    # This endpoint helps visualize resource contention
    
    # CPU stress
    data = b"combined_stress_test"
    for _ in range(config.cpuStressRounds // 2):  # Use half rounds to keep response time reasonable
        data = hashlib.sha256(data).digest()
    
    # Memory stress
    memory_chunks = []
    bytes_per_mb = 1024 * 1024
    chunk_size = 1024 * 100
    
    try:
        for _ in range(0, config.memoryStressMb * bytes_per_mb, chunk_size):
            chunk = bytearray(random.getrandbits(8) for _ in range(chunk_size))
            memory_chunks.append(chunk)
        
        # Process the memory while holding it (simulates real workload)
        result = sum(len(chunk) for chunk in memory_chunks)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Combined stress test completed",
                "cpu_rounds": config.cpuStressRounds // 2,
                "memory_mb": config.memoryStressMb,
                "total_bytes": result,
                "hash": data.hex()[:16]
            }
        )
    finally:
        memory_chunks.clear()
        del memory_chunks


# ============================================================================
# ADMIN ENDPOINT - Config Updates (Teaching: Live system tuning)
# ============================================================================

class AdminConfigPatch(BaseModel):
    """Pydantic model for config updates."""
    poolEnabled: Optional[bool] = Field(None, description="Enable/disable connection pool")
    poolMax: Optional[int] = Field(None, ge=1, le=100, description="Max connections in pool")
    poolWaitTimeoutMs: Optional[int] = Field(None, ge=10, le=5000, description="Pool wait timeout in ms")
    loginCpuRounds: Optional[int] = Field(None, ge=1, le=1000000, description="CPU burn rounds for login")
    cpuStressRounds: Optional[int] = Field(None, ge=1, le=10000000, description="CPU stress rounds for /stress/cpu endpoint")
    memoryStressMb: Optional[int] = Field(None, ge=1, le=500, description="Memory stress in MB for /stress/memory endpoint")
    checkoutFailRate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Checkout failure rate (0.0-1.0)")


@app.post("/admin/config")
async def update_config(patch: AdminConfigPatch):
    """
    Update runtime configuration.
    
    TEACHING PURPOSE: Allows live tuning during workshop to demonstrate
    how config changes affect performance metrics.
    """
    updates = patch.dict(exclude_unset=True)
    await config.update(**updates)
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Config updated",
            "config": {
                "poolEnabled": config.poolEnabled,
                "poolMax": config.poolMax,
                "poolWaitTimeoutMs": config.poolWaitTimeoutMs,
                "loginCpuRounds": config.loginCpuRounds,
                "cpuStressRounds": config.cpuStressRounds,
                "memoryStressMb": config.memoryStressMb,
                "checkoutFailRate": config.checkoutFailRate
            }
        }
    )


@app.get("/admin/config")
async def get_config():
    """Get current configuration."""
    return JSONResponse(
        status_code=200,
        content={
            "poolEnabled": config.poolEnabled,
            "poolMax": config.poolMax,
            "poolWaitTimeoutMs": config.poolWaitTimeoutMs,
            "loginCpuRounds": config.loginCpuRounds,
            "cpuStressRounds": config.cpuStressRounds,
            "memoryStressMb": config.memoryStressMb,
            "checkoutFailRate": config.checkoutFailRate
        }
    )
