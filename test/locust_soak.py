"""
Soak Test - Endurance test with stable moderate load

TEACHING PURPOSE:
- Tests system stability over extended period
- Identifies memory leaks, resource exhaustion
- Validates system can handle sustained load
- Run for 30+ minutes

Run: locust -f test/locust_soak.py --host http://localhost:8000 --users 30 --spawn-rate 3 --run-time 30m
"""
import random
from locust import between, task
from test.locust_common import BaseEcommerceUser, pick_product_id


class SoakTestUser(BaseEcommerceUser):
    """
    Soak test user - stable moderate load for extended period.
    """
    wait_time = between(1.0, 3.0)  # Realistic user behavior
    
    @task(10)
    def browse_products(self):
        """Browse products"""
        page = random.randint(1, 10)
        self.client.get(f"/products?page={page}&limit=20", name="GET /products")
    
    @task(8)
    def view_product_detail(self):
        """View product detail"""
        product_id = pick_product_id()
        self.client.get(f"/products/{product_id}", name="GET /products/{id}")
    
    @task(2)
    def do_login(self):
        """Login"""
        if not self.token:
            self.login()
    
    @task(3)
    def add_to_cart(self):
        """Add to cart"""
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
        """Checkout"""
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
