"""
FastAPI Demo API for Performance Testing Workshop

This API is designed to demonstrate various performance bottlenecks
and testing scenarios for educational purposes.
"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import engine, AsyncSessionLocal, Base
from app.models import Product, AppConfig
from app.routers import health, auth, products, cart, admin, heavy
from app.migrations import run_migrations
from sqlalchemy import text

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "request_id": "%(name)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global app config
app_config = AppConfig()


async def seed_products_minimal():
    """
    Seed database with minimal products on startup (if none exist).
    For massive data, use the seed_data.py script separately.
    TEACHING PURPOSE: Provides basic product data for quick startup.
    """
    logger.info("Checking for existing products...")
    async with AsyncSessionLocal() as session:
        # Check if products already exist
        result = await session.execute(select(Product).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("Products already exist, skipping minimal seeding...")
            return
        
        # Create minimal 10,000 products for quick startup
        logger.info("Seeding minimal 10,000 products (use seed_data.py for massive data)...")
        products = []
        for i in range(1, 10001):
            products.append(Product(
                id=i,
                name=f"Product {i}",
                price=round(10.0 + (i % 100) * 0.5, 2),
                stock=100,  # Initial stock
                description=f"Description for Product {i}"
            ))
            
            # Batch insert every 1000 products
            if len(products) >= 1000:
                session.add_all(products)
                await session.commit()
                products = []
                logger.info(f"Seeded {i} products...")
        
        # Insert remaining products
        if products:
            session.add_all(products)
            await session.commit()
        
        logger.info("Finished seeding minimal 10,000 products")


async def fix_cart_items_sequence():
    """
    Fix the cart_items sequence to start from max(id) + 1.
    This handles the case where data was seeded manually with specific IDs.
    TEACHING PURPOSE: Demonstrates sequence management in PostgreSQL.
    """
    logger.info("Checking cart_items sequence...")
    async with AsyncSessionLocal() as session:
        try:
            # Get max ID from cart_items
            result = await session.execute(text("SELECT COALESCE(MAX(id), 0) FROM cart_items"))
            max_id = result.scalar() or 0
            
            # Create sequence if it doesn't exist and set it to max_id + 1
            await session.execute(text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_sequences WHERE sequencename = 'cart_items_id_seq'
                    ) THEN
                        CREATE SEQUENCE cart_items_id_seq;
                    END IF;
                    PERFORM setval('cart_items_id_seq', GREATEST({max_id}, 1), true);
                    ALTER TABLE cart_items ALTER COLUMN id SET DEFAULT nextval('cart_items_id_seq');
                END $$;
            """))
            await session.commit()
            logger.info(f"Cart items sequence fixed (max_id: {max_id})")
        except Exception as e:
            logger.warning(f"Could not fix cart_items sequence: {e}. This is OK if migration handles it.")
            await session.rollback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup (DB creation, seeding) and shutdown.
    """
    # Startup
    logger.info("Starting application...")
    
    # Run database migrations
    logger.info("Running database migrations...")
    run_migrations()  # Alembic handles async internally
    logger.info("Database migrations completed")
    
    # Fix cart_items sequence if needed (handles case where data was seeded manually)
    await fix_cart_items_sequence()
    
    # Seed minimal products (if none exist)
    await seed_products_minimal()
    
    # Inject config into routers
    auth.set_config(app_config)
    products.set_config(app_config)
    cart.set_config(app_config)
    admin.set_config(app_config)
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Performance Testing Demo API",
    description="Demo API for Locust performance testing workshop",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(admin.router)
app.include_router(heavy.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log requests with structured logging.
    TEACHING PURPOSE: Demonstrates request tracking and observability.
    """
    request_id = str(uuid4())
    start_time = asyncio.get_event_loop().time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    
    # Log request
    logger.info(
        f"request_id={request_id} "
        f"method={request.method} "
        f"path={request.url.path} "
        f"status_code={response.status_code} "
        f"latency_ms={latency_ms:.2f}"
    )
    
    return response


if __name__ == "__main__":
    import uvicorn
    from app.settings import settings
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
