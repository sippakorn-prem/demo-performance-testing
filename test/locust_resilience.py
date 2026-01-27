"""
Resilience Test - Introduce failures during load test

TEACHING PURPOSE:
- Tests system resilience to failures
- Runs load test while introducing failures via /admin/failure
- Shows how system handles partial failures
- Demonstrates error handling and recovery

Run: locust -f test/locust_resilience.py --host http://localhost:8000 --users 50 --spawn-rate 5

Then in another terminal, introduce failures:
  curl -X POST http://localhost:8000/admin/failure -H "Content-Type: application/json" -d '{"checkout": 0.1}'
"""
import random
import time
import threading
from locust import between, task
from test.locust_common import BaseEcommerceUser, pick_product_id


class ResilienceTestUser(BaseEcommerceUser):
    """
    Resilience test user - normal load while failures are introduced.
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
        """Checkout - will see failures when admin introduces them"""
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
