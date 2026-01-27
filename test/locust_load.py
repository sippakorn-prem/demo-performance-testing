"""
Load Test - Expected production traffic

TEACHING PURPOSE:
- Simulates expected production load
- Tests system under normal operating conditions
- Validates system can handle expected traffic

Run: locust -f test/locust_load.py --host http://localhost:8000 --users 50 --spawn-rate 5
"""
import random
from locust import between, task
from test.locust_common import BaseEcommerceUser, pick_product_id


class LoadTestUser(BaseEcommerceUser):
    """
    Load test user - simulates expected production traffic.
    """
    wait_time = between(0.5, 2.0)  # Realistic user behavior
    
    @task(10)
    def browse_products(self):
        """Browse products - most common"""
        page = 1
        self.client.get(f"/products?page={page}&limit=20", name="GET /products")
    
    @task(8)
    def view_product_detail(self):
        """View product detail - common"""
        product_id = pick_product_id(hot_bias=0.8)
        self.client.get(f"/products/{product_id}", name="GET /products/{id}")
    
    @task(2)
    def do_login(self):
        """Login - occasional"""
        if not self.token:
            self.login()
    
    @task(3)
    def add_to_cart(self):
        """Add to cart - requires auth"""
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
        """Checkout - rare (conversion rate ~5%)"""
        if not self.token:
            self.login()
        
        if self.token and random.random() < 0.05:  # 5% conversion
            product_id = pick_product_id()
            self.client.post(
                "/cart/checkout",
                json={"product_id": product_id, "quantity": 1},
                headers=self.get_auth_headers(),
                name="POST /cart/checkout"
            )
