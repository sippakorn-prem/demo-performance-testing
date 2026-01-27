"""
Stress Test - Gradually increase load until system breaks

TEACHING PURPOSE:
- Finds system breaking point
- Identifies maximum capacity
- Shows how system degrades under stress
- Uses LoadTestShape for staged ramp-up

Run: locust -f test/locust_stress.py --host http://localhost:8000
"""
import random
from locust import between, task, LoadTestShape
from test.locust_common import BaseEcommerceUser, pick_product_id


class StressTestUser(BaseEcommerceUser):
    """
    Stress test user - includes heavy load endpoints to stress different resources.
    """
    wait_time = between(0.5, 2.0)
    
    @task(10)
    def browse_products(self):
        self.client.get("/products?page=1&limit=20", name="GET /products")
    
    @task(8)
    def view_product_detail(self):
        product_id = pick_product_id()
        self.client.get(f"/products/{product_id}", name="GET /products/{id}")
    
    @task(2)
    def do_login(self):
        if not self.token:
            self.login()
    
    @task(3)
    def add_to_cart(self):
        if not self.token:
            self.login()
        
        if self.token:
            product_id = pick_product_id()
            self.client.post(
                "/cart/items",
                json={"product_id": product_id, "quantity": 1},
                headers=self.get_auth_headers(),
                name="POST /cart/items"
            )
    
    @task(1)
    def checkout(self):
        if not self.token:
            self.login()
        
        if self.token and random.random() < 0.05:
            product_id = pick_product_id()
            self.client.post(
                "/cart/checkout",
                json={"product_id": product_id, "quantity": 1},
                headers=self.get_auth_headers(),
                name="POST /cart/checkout"
            )
    
    # Heavy load endpoints for stress testing
    @task(5)
    def cpu_heavy(self):
        """CPU-intensive endpoint - stresses CPU"""
        iterations = random.randint(50000, 200000)
        rounds = random.randint(5, 15)
        self.client.get(
            f"/heavy/cpu?iterations={iterations}&rounds={rounds}",
            name="GET /heavy/cpu"
        )
    
    @task(3)
    def memory_heavy(self):
        """Memory-intensive endpoint - stresses memory"""
        size_mb = random.randint(5, 20)
        chunks = random.randint(3, 10)
        self.client.get(
            f"/heavy/memory?size_mb={size_mb}&chunks={chunks}",
            name="GET /heavy/memory"
        )
    
    @task(4)
    def latency_heavy(self):
        """Latency-intensive endpoint - introduces delays"""
        delay_ms = random.randint(200, 1000)
        steps = random.randint(1, 3)
        self.client.get(
            f"/heavy/latency?delay_ms={delay_ms}&steps={steps}",
            name="GET /heavy/latency"
        )
    
    @task(6)
    def database_heavy(self):
        """Database-intensive endpoint - stresses PostgreSQL"""
        complexity = random.randint(3, 8)
        joins = random.choice([True, False])
        aggregations = random.choice([True, False])
        self.client.get(
            f"/heavy/database?complexity={complexity}&joins={joins}&aggregations={aggregations}",
            name="GET /heavy/database"
        )
    
    @task(2)
    def mixed_heavy(self):
        """Mixed load endpoint - combines all resource types"""
        cpu_iterations = random.randint(30000, 100000)
        memory_mb = random.randint(3, 10)
        delay_ms = random.randint(50, 200)
        db_queries = random.randint(2, 5)
        self.client.get(
            f"/heavy/mixed?cpu_iterations={cpu_iterations}&memory_mb={memory_mb}&delay_ms={delay_ms}&db_queries={db_queries}",
            name="GET /heavy/mixed"
        )


class StagedRampUpLoadShape(LoadTestShape):
    """
    Staged ramp-up load shape for stress testing.
    
    TEACHING PURPOSE:
    - Gradually increases load in stages
    - Allows observation of system behavior at each stage
    - Helps identify breaking point
    
    Stages:
    - 0-60s: 10 users
    - 60-120s: 25 users
    - 120-180s: 50 users
    - 180-240s: 100 users
    - 240-300s: 150 users
    - 300+: 200 users (or until system breaks)
    """
    
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 120, "users": 25, "spawn_rate": 3},
        {"duration": 180, "users": 50, "spawn_rate": 5},
        {"duration": 240, "users": 100, "spawn_rate": 10},
        {"duration": 300, "users": 150, "spawn_rate": 15},
        {"duration": 360, "users": 200, "spawn_rate": 20},
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
        
        # Continue at max load
        return (200, 20)
