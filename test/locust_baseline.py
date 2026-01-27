"""
Baseline Test - Small load to establish baseline metrics

TEACHING PURPOSE:
- Establishes baseline performance metrics
- Low user count to avoid stressing the system
- Use results as reference for other tests

Run: locust -f test/locust_baseline.py --host http://localhost:8000
"""
from locust import between, task
from test.locust_common import BaseEcommerceUser, pick_product_id


class BaselineUser(BaseEcommerceUser):
    """
    Baseline test user - minimal load to establish baseline.
    """
    wait_time = between(1.0, 3.0)  # Realistic user behavior
    
    @task(5)
    def browse_products(self):
        """Browse products list - most common action"""
        self.client.get("/products?page=1&limit=20", name="GET /products")
    
    @task(3)
    def view_product_detail(self):
        """View product detail - common action"""
        product_id = pick_product_id()
        self.client.get(f"/products/{product_id}", name="GET /products/{id}")
    
    @task(1)
    def do_login(self):
        """Login - less common"""
        if not self.token:
            self.login()
    
    @task(1)
    def add_to_cart(self):
        """Add to cart - requires authentication"""
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
        """Checkout - rare action"""
        if not self.token:
            self.login()
        
        if self.token:
            product_id = pick_product_id()
            self.client.post(
                "/cart/checkout",
                json={"product_id": product_id, "quantity": 1},
                headers=self.get_auth_headers(),
                name="POST /cart/checkout"
            )
