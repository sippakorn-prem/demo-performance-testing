"""
Simple Locust script to load test the demo FastAPI app.

Endpoints under test:
- GET /hello       -> very fast, baseline endpoint
- GET /cpu-heavy   -> burns CPU for a short time
- GET /ram-heavy   -> allocates some memory

How to run (from this directory):
  locust -f locust.py --host=http://localhost:8000

Then open the Locust web UI (by default http://localhost:8089),
set number of users and spawn rate, and start the test.
"""

from locust import HttpUser, between, task


class SimplePerformanceTester(HttpUser):
    """
    Basic user behavior for performance testing.

    - Mostly calls /hello (cheap request)
    - Sometimes calls /cpu-heavy and /ram-heavy (expensive requests)
    """

    host = "http://localhost:8000"
    # Wait between 0.2 and 1 second between each request
    wait_time = between(0.2, 1.0)

    @task(5)
    def hello(self) -> None:
        self.client.get("/hello")

    @task(2)
    def cpu_heavy(self) -> None:
        """CPU-heavy endpoint: burns CPU for ~1 second."""
        self.client.get("/cpu-heavy", params={"seconds": 1.0})

    @task(1)
    def ram_heavy(self) -> None:
        """RAM-heavy endpoint: allocates ~100 MB."""
        self.client.get("/ram-heavy", params={"megabytes": 100})

