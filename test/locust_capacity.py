"""
Capacity Test - Stepwise load increase with SLO validation

TEACHING PURPOSE:
- Tests system capacity against SLOs (Service Level Objectives)
- Validates p95 < 300ms and error rate < 1%
- Stepwise load increase
- Logs PASS/FAIL at each step

Run: locust -f test/locust_capacity.py --host http://localhost:8000
"""
import random
import logging
from locust import between, task, LoadTestShape, events
from test.locust_common import BaseEcommerceUser, pick_product_id

# Configure logging
logger = logging.getLogger(__name__)

# SLO thresholds
SLO_P95_MS = 300  # p95 latency must be < 300ms
SLO_ERROR_RATE = 0.01  # Error rate must be < 1%


class CapacityTestUser(BaseEcommerceUser):
    """
    Capacity test user - realistic user behavior.
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


class StepwiseLoadShape(LoadTestShape):
    """
    Stepwise load increase for capacity testing.
    
    Each step runs for 2 minutes to collect stable metrics.
    """
    
    steps = [
        {"duration": 120, "users": 10, "spawn_rate": 2},
        {"duration": 240, "users": 25, "spawn_rate": 3},
        {"duration": 360, "users": 50, "spawn_rate": 5},
        {"duration": 480, "users": 75, "spawn_rate": 8},
        {"duration": 600, "users": 100, "spawn_rate": 10},
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for i, step in enumerate(self.steps):
            if run_time < step["duration"]:
                # Check SLOs at end of each step (last 30 seconds)
                if run_time > step["duration"] - 30 and run_time < step["duration"] - 10:
                    self._check_slos(step["users"])
                
                return (step["users"], step["spawn_rate"])
        
        return None
    
    def _check_slos(self, current_users):
        """Check SLOs and log PASS/FAIL"""
        # This would need access to stats - simplified version
        # In real implementation, you'd query Locust stats API
        logger.info(f"Checking SLOs at {current_users} users...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - validate final SLOs"""
    stats = environment.stats
    
    # Calculate overall metrics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    error_rate = total_failures / total_requests if total_requests > 0 else 0
    
    # Get p95 latency (in milliseconds)
    p95_ms = stats.total.get_response_time_percentile(0.95)
    
    # Check SLOs
    p95_pass = p95_ms < SLO_P95_MS
    error_pass = error_rate < SLO_ERROR_RATE
    
    # Log results
    logger.info("=" * 60)
    logger.info("CAPACITY TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total Requests: {total_requests}")
    logger.info(f"Total Failures: {total_failures}")
    logger.info(f"Error Rate: {error_rate:.2%}")
    logger.info(f"p95 Latency: {p95_ms:.2f}ms")
    logger.info("")
    logger.info("SLO Validation:")
    logger.info(f"  p95 < {SLO_P95_MS}ms: {'PASS' if p95_pass else 'FAIL'} ({p95_ms:.2f}ms)")
    logger.info(f"  Error Rate < {SLO_ERROR_RATE:.1%}: {'PASS' if error_pass else 'FAIL'} ({error_rate:.2%})")
    logger.info("")
    logger.info(f"Overall: {'PASS' if (p95_pass and error_pass) else 'FAIL'}")
    logger.info("=" * 60)
