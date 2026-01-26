"""
Locust Performance Test File

This file simulates realistic user behavior for the performance testing workshop.
Each task represents a different user action with appropriate weights.

TEACHING PURPOSE: Show how to write realistic load tests that mirror actual usage patterns.
"""

from locust import HttpUser, task, between


class DemoAPIUser(HttpUser):
    """
    Simulates a user interacting with the demo API.
    
    TEACHING PURPOSE: This class represents a single "user" that will execute
    tasks with realistic wait times between actions.
    """
    
    # Teaching: Wait time between tasks simulates user thinking/reading time
    # between(0.2, 1.0) means 200ms to 1 second between actions
    wait_time = between(0.2, 1.0)
    
    def on_start(self):
        """
        Called when a user starts.
        
        TEACHING PURPOSE: Optional setup that runs once per user.
        Could be used for authentication, but we skip it for simplicity.
        """
        pass
    
    @task(5)
    def browse_products(self):
        """
        Browse products list - highest weight (most common action).
        
        TEACHING PURPOSE: 
        - Weight 5 means this is 5x more likely than weight 1 tasks
        - Demonstrates baseline latency (100-300ms)
        - Shows how high-frequency endpoints affect overall RPS
        """
        self.client.get("/products", name="GET /products")
    
    @task(3)
    def view_product_detail(self):
        """
        View individual product - medium weight.
        
        TEACHING PURPOSE:
        - Weight 3 means moderate frequency
        - Uses connection pool (can show 503 errors when pool is exhausted)
        - Demonstrates resource contention
        """
        product_id = 1  # Simple: always check product 1
        self.client.get(f"/products/{product_id}", name="GET /products/{id}")
    
    @task(2)
    def login(self):
        """
        User login - lower weight (less frequent).
        
        TEACHING PURPOSE:
        - Weight 2 means less frequent but still common
        - CPU-intensive task (shows CPU bottleneck when loginCpuRounds is high)
        - Demonstrates how CPU-bound tasks affect response times
        """
        self.client.post("/login", name="POST /login")
    
    @task(1)
    def checkout(self):
        """
        Checkout - lowest weight (least frequent but critical).
        
        TEACHING PURPOSE:
        - Weight 1 means least frequent (checkout happens less than browsing)
        - Uses connection pool (can show 503 errors)
        - Has configurable failure rate (shows error rate monitoring)
        - Demonstrates how critical paths affect user experience
        """
        self.client.post("/checkout", name="POST /checkout")
    
    @task(1)
    def heavy_endpoint(self):
        """
        Heavy computation endpoint - low weight.
        
        TEACHING PURPOSE:
        - Weight 1 means occasional use
        - High latency (800-1200ms) shows impact on p95 metrics
        - Demonstrates how slow endpoints affect overall system performance
        """
        self.client.get("/heavy", name="GET /heavy")
