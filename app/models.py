"""
SQLAlchemy models for the demo application
"""
import asyncio
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base


class Product(Base):
    """Product model - seeded with 10,000 products"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=100, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationships
    cart_items = relationship("CartItem", back_populates="product")


class CartItem(Base):
    """Cart item model"""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="cart_items")


class AppConfig:
    """
    Application configuration for teaching purposes.
    Allows live updates during workshop to demonstrate different bottlenecks.
    """
    def __init__(self):
        # Auth settings
        self.auth_hashing_rounds: int = 10000
        
        # Latency settings (milliseconds)
        self.latency_auth_ms: float = 0
        self.latency_products_ms: float = 0
        self.latency_checkout_ms: float = 0
        
        # Failure rate settings (0.0 to 1.0)
        self.failure_rate_auth: float = 0.0
        self.failure_rate_products: float = 0.0
        self.failure_rate_checkout: float = 0.0
        
        # Cache settings
        self.cache_enabled: bool = True
        self.cache_hit_ratio: float = 0.7  # 70% cache hit rate
        
        # Lock for thread-safety
        self._lock = asyncio.Lock()
    
    async def update(self, **kwargs):
        """Update configuration values (thread-safe)"""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
