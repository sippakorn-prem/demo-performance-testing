"""
Concurrency Test - All users checkout same product simultaneously

TEACHING PURPOSE:
- Tests race conditions in stock management
- All users target same product_id (e.g., product_id=1)
- No wait_time to maximize concurrent requests
- Measures 409 (conflict) and 500 errors
- Demonstrates need for proper locking/transactions

Run: locust -f test/locust_concurrency.py --host http://localhost:8000 --users 100 --spawn-rate 20
"""
from locust import task
from test.locust_common import BaseEcommerceUser


# All users will checkout the same product to create race condition
TARGET_PRODUCT_ID = 1


class ConcurrencyTestUser(BaseEcommerceUser):
    """
    Concurrency test user - all users checkout same product.
    """
    wait_time = 0  # No wait - maximize concurrent requests
    
    def on_start(self):
        """Login on start"""
        super().on_start()
        if not self.token:
            self.login()
    
    @task(1)
    def checkout_same_product(self):
        """
        All users checkout the same product simultaneously.
        
        TEACHING PURPOSE:
        - Creates race condition on stock management
        - Should see 409 (Conflict) errors when stock runs out
        - Demonstrates need for proper database transactions/locking
        """
        if self.token:
            self.client.post(
                "/cart/checkout",
                json={"product_id": TARGET_PRODUCT_ID, "quantity": 1},
                headers=self.get_auth_headers(),
                name="POST /cart/checkout (concurrency test)"
            )
