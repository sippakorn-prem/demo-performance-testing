import time
import random
from typing import Any, Dict, List

from fastapi import FastAPI, Query, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Simple Perf Demo API")

# Add Prometheus metrics endpoint at /metrics
Instrumentator().instrument(app).expose(app)


@app.get("/hello")
async def hello() -> Dict[str, str]:
    """
    Simple hello endpoint with occasional 500 errors for demo.

    Roughly 10% of requests will return HTTP 500 to drive
    the "Error Rate (5xx)" panel in Grafana / Prometheus.
    """
    # random 500 error status code (~10% of the time)
    if random.random() < 0.1:
        raise HTTPException(status_code=500, detail="Random demo error")

    return {"message": "Hello from FastAPI!"}


@app.get("/cpu-heavy")
def cpu_heavy(seconds: float = 5.0) -> Dict[str, Any]:
    start = time.time()
    while time.time() - start < seconds:
        # do some useless work so the CPU is busy
        _ = 1 + 1

    return {"seconds": seconds}


@app.get("/ram-heavy")
def ram_heavy(megabytes: int = 100) -> Dict[str, Any]:
    size_bytes = megabytes * 1024 * 1024
    _data = bytearray(size_bytes)

    return {"allocated_mb": megabytes}


# Quick hint for running locally:
#   uvicorn app:app --reload

