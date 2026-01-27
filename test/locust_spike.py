"""
Spike Test - Sudden traffic spike

TEACHING PURPOSE:
- Tests system response to sudden traffic increase
- Simulates flash sale, viral content, etc.
- Shows if system can handle sudden load spikes
- No wait_time for maximum load

Run: locust -f test/locust_spike.py --host http://localhost:8000 --users 200 --spawn-rate 50
"""
import random
from locust import task
from test.locust_common import BaseEcommerceUser, pick_product_id


class SpikeTestUser(BaseEcommerceUser):
    """
    Spike test user - no wait time to maximize load.
    """
    wait_time = 0  # No wait - maximum load
    
    @task(10)
    def browse_products(self):
        """Browse products"""
        self.client.get("/products?page=1&limit=20", name="GET /products")
    
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
