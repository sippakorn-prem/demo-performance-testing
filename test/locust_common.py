"""
Common helpers for Locust test scripts
"""
import random
from locust import HttpUser, task


# Hot product IDs (most popular products - will have more traffic)
HOT_PRODUCT_IDS = [1, 2, 3, 4, 5, 10, 20, 50, 100, 500]


def login_user(client, email: str = "test@example.com", password: str = "password") -> str:
    """
    Helper to login a user and return access token.
    
    Args:
        client: Locust HttpUser client
        email: User email
        password: User password
        
    Returns:
        access_token or None if login failed
    """
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
        name="POST /auth/login"
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None


def get_auth_headers(token: str) -> dict:
    """Get authorization headers for authenticated requests"""
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def pick_product_id(hot_bias: float = 0.8) -> int:
    """
    Pick a product ID with bias towards hot products.
    
    Args:
        hot_bias: Probability of picking a hot product (0.0-1.0)
        
    Returns:
        Product ID (1-10000)
    """
    if random.random() < hot_bias:
        return random.choice(HOT_PRODUCT_IDS)
    return random.randint(1, 10000)


class BaseEcommerceUser(HttpUser):
    """
    Base user class with common functionality.
    All test user classes should inherit from this.
    
    NOTE: This class is marked as abstract to prevent Locust from trying to
    instantiate it directly. Only subclasses should be used in tests.
    """
    abstract = True  # Prevents Locust from instantiating this base class
    host = "http://localhost:8000"  # Default host for all tests
    wait_time = None  # Override in subclasses
    
    # Dummy task as fallback if abstract flag isn't recognized by Locust
    # This should never be called since abstract=True should prevent instantiation
    # and subclasses will have their own tasks
    @task(1)
    def _dummy_base_task(self):
        """Dummy task - should never be called if abstract=True works correctly"""
        pass
    
    def on_start(self):
        """Called when a user starts"""
        self.token = None
        self.user_id = None
        
        # 30% of users start logged in
        if random.random() < 0.3:
            self.token = login_user(self.client)
            if self.token:
                self.user_id = random.randint(1, 1000)
    
    def login(self):
        """Login helper"""
        self.token = login_user(self.client)
        if self.token:
            self.user_id = random.randint(1, 1000)
    
    def get_auth_headers(self) -> dict:
        """Get auth headers if logged in"""
        return get_auth_headers(self.token)
