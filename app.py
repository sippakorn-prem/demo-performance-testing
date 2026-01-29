import time
from typing import Any, Dict, List

from fastapi import FastAPI, Query

app = FastAPI(title="Simple Perf Demo API")


@app.get("/hello")
async def hello() -> Dict[str, str]:
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

