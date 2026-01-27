"""
Data Seeder Script for Performance Testing Workshop

Generates massive amounts of example data for all test scenarios:
- Products (100,000+)
- Cart items for multiple users
- Various stock levels for concurrency testing
- Realistic product data

Run: python -m app.seed_data
Or: python app/seed_data.py

Options:
  --products N      Number of products to seed (default: 100000)
  --users N         Number of users for cart items (default: 1000)
  --items-per-user N  Average items per user (default: 5)
  --skip-cart       Skip cart item seeding
  --skip-low-stock  Skip low-stock product creation
"""
import argparse
import asyncio
import random
import sys
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func, delete
from app.db import Base
from app.models import Product, CartItem
from app.settings import settings
from app.migrations import run_migrations


# Product categories for realistic names
CATEGORIES = [
    "Electronics", "Clothing", "Books", "Home & Garden", "Sports",
    "Toys", "Beauty", "Automotive", "Food", "Health",
    "Furniture", "Jewelry", "Tools", "Pet Supplies", "Office"
]

ADJECTIVES = [
    "Premium", "Deluxe", "Professional", "Standard", "Basic",
    "Advanced", "Classic", "Modern", "Vintage", "Luxury",
    "Economy", "Pro", "Elite", "Essential", "Ultimate"
]

NOUNS = [
    "Widget", "Gadget", "Device", "Tool", "Item",
    "Product", "Solution", "System", "Kit", "Set",
    "Bundle", "Package", "Collection", "Series", "Model"
]


def generate_product_name(product_id: int) -> str:
    """Generate realistic product name"""
    category = random.choice(CATEGORIES)
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    
    # Mix of formats for variety
    formats = [
        f"{adjective} {category} {noun} {product_id}",
        f"{category} {adjective} {noun} - {product_id}",
        f"{adjective} {noun} for {category} - #{product_id}",
        f"{category} {noun} {product_id} ({adjective})",
    ]
    
    return random.choice(formats)


def generate_price(product_id: int) -> float:
    """Generate realistic price"""
    # Price ranges from $5 to $999.99
    base_price = random.uniform(5.0, 999.99)
    
    # Some products are more expensive (luxury items)
    if product_id % 100 == 0:
        base_price *= random.uniform(2, 5)
    
    return round(base_price, 2)


def generate_stock(product_id: int) -> int:
    """Generate stock level with some low-stock items for concurrency testing"""
    # Most products have good stock
    if random.random() < 0.7:
        return random.randint(50, 1000)
    
    # 20% have medium stock
    elif random.random() < 0.9:
        return random.randint(10, 50)
    
    # 10% have low stock (for concurrency testing)
    else:
        return random.randint(1, 10)


def generate_description(product_id: int, name: str) -> str:
    """Generate product description"""
    category = random.choice(CATEGORIES)
    features = [
        "High quality materials",
        "Durable construction",
        "Easy to use",
        "Professional grade",
        "Energy efficient",
        "Eco-friendly",
        "Compact design",
        "Multi-functional",
        "Long-lasting",
        "Premium finish"
    ]
    
    feature = random.choice(features)
    return f"{name} is a {category.lower()} product featuring {feature.lower()}. Perfect for your needs. Product ID: {product_id}"


async def seed_products(session: AsyncSession, num_products: int = 100000, batch_size: int = 1000):
    """
    Seed products in batches for efficiency.
    
    Args:
        session: Database session
        num_products: Total number of products to create
        batch_size: Number of products per batch
    """
    print(f"🌱 Seeding {num_products:,} products...")
    
    # Check existing count
    result = await session.execute(select(func.count(Product.id)))
    existing_count = result.scalar()
    
    if existing_count >= num_products:
        print(f"✅ Already have {existing_count:,} products. Skipping product seeding.")
        return
    
    # Delete existing if fewer than requested
    if existing_count > 0 and existing_count < num_products:
        print(f"⚠️  Found {existing_count:,} existing products. Deleting to reseed...")
        await session.execute(delete(Product))
        await session.commit()
        existing_count = 0
    
    start_id = existing_count + 1
    total_batches = (num_products - existing_count + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        batch_start = start_id + (batch_num * batch_size)
        batch_end = min(batch_start + batch_size, start_id + num_products)
        batch_size_actual = batch_end - batch_start
        
        products = []
        for i in range(batch_start, batch_end):
            products.append(Product(
                id=i,
                name=generate_product_name(i),
                price=generate_price(i),
                stock=generate_stock(i),
                description=generate_description(i, f"Product {i}")
            ))
        
        session.add_all(products)
        await session.commit()
        
        progress = ((batch_num + 1) / total_batches) * 100
        print(f"  Progress: {progress:.1f}% - Seeded products {batch_start:,} to {batch_end-1:,} ({batch_size_actual:,} products)")
    
    print(f"✅ Successfully seeded {num_products:,} products!")


async def seed_cart_items(session: AsyncSession, num_users: int = 1000, items_per_user: int = 5):
    """
    Seed cart items for multiple users.
    
    Args:
        session: Database session
        num_users: Number of users to create cart items for
        items_per_user: Average number of items per user
    """
    print(f"🛒 Seeding cart items for {num_users:,} users...")
    
    # Check existing count
    result = await session.execute(select(func.count(CartItem.id)))
    existing_count = result.scalar()
    
    if existing_count > 0:
        print(f"⚠️  Found {existing_count:,} existing cart items. Deleting to reseed...")
        await session.execute(delete(CartItem))
        await session.commit()
    
    # Get product IDs
    result = await session.execute(select(Product.id).limit(10000))
    product_ids = [row[0] for row in result.fetchall()]
    
    if not product_ids:
        print("❌ No products found. Please seed products first.")
        return
    
    total_items = num_users * items_per_user
    batch_size = 500
    total_batches = (total_items + batch_size - 1) // batch_size
    
    item_id = 1
    for batch_num in range(total_batches):
        cart_items = []
        batch_items = min(batch_size, total_items - (batch_num * batch_size))
        
        for _ in range(batch_items):
            user_id = random.randint(1, num_users)
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 3)
            
            cart_items.append(CartItem(
                id=item_id,
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            ))
            item_id += 1
        
        session.add_all(cart_items)
        await session.commit()
        
        progress = ((batch_num + 1) / total_batches) * 100
        print(f"  Progress: {progress:.1f}% - Seeded {item_id:,} cart items")
    
    print(f"✅ Successfully seeded cart items for {num_users:,} users!")


async def create_low_stock_products(session: AsyncSession, num_products: int = 100):
    """
    Create specific low-stock products for concurrency testing.
    Sets stock to exactly 1 for targeted testing.
    
    Args:
        session: Database session
        num_products: Number of products to set to low stock
    """
    print(f"⚠️  Creating {num_products} low-stock products for concurrency testing...")
    
    # Get first N products and set stock to 1
    result = await session.execute(
        select(Product).limit(num_products)
    )
    products = result.scalars().all()
    
    for product in products:
        product.stock = 1
    
    await session.commit()
    print(f"✅ Set {len(products)} products to stock=1 for concurrency testing")


async def create_hot_products(session: AsyncSession, product_ids: list):
    """
    Ensure specific product IDs exist and have good stock (for hot product testing).
    
    Args:
        session: Database session
        product_ids: List of product IDs to ensure exist
    """
    print(f"🔥 Ensuring hot products exist: {product_ids}...")
    
    for product_id in product_ids:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if product:
            # Ensure good stock for hot products
            product.stock = random.randint(500, 1000)
        else:
            # Create if doesn't exist
            product = Product(
                id=product_id,
                name=f"Hot Product {product_id}",
                price=generate_price(product_id),
                stock=random.randint(500, 1000),
                description=f"Popular hot product {product_id}"
            )
            session.add(product)
    
    await session.commit()
    print(f"✅ Hot products ready!")


async def print_statistics(session: AsyncSession):
    """Print database statistics"""
    print("\n📊 Database Statistics:")
    print("=" * 60)
    
    # Product stats
    result = await session.execute(select(func.count(Product.id)))
    product_count = result.scalar()
    
    result = await session.execute(
        select(func.sum(Product.stock))
    )
    total_stock = result.scalar() or 0
    
    result = await session.execute(
        select(func.avg(Product.price))
    )
    avg_price = result.scalar() or 0
    
    result = await session.execute(
        select(func.count(Product.id)).where(Product.stock < 10)
    )
    low_stock_count = result.scalar()
    
    print(f"Products: {product_count:,}")
    print(f"Total Stock: {total_stock:,}")
    print(f"Average Price: ${avg_price:.2f}")
    print(f"Low Stock Products (<10): {low_stock_count:,}")
    
    # Cart item stats
    result = await session.execute(select(func.count(CartItem.id)))
    cart_count = result.scalar()
    
    if cart_count > 0:
        result = await session.execute(
            select(func.count(func.distinct(CartItem.user_id)))
        )
        user_count = result.scalar()
        
        print(f"\nCart Items: {cart_count:,}")
        print(f"Users with Cart Items: {user_count:,}")
    
    print("=" * 60)


async def main():
    """Main seeding function"""
    parser = argparse.ArgumentParser(description="Seed database with massive test data")
    parser.add_argument("--products", type=int, default=100000, help="Number of products to seed (default: 100000)")
    parser.add_argument("--users", type=int, default=1000, help="Number of users for cart items (default: 1000)")
    parser.add_argument("--items-per-user", type=int, default=5, help="Average items per user (default: 5)")
    parser.add_argument("--skip-cart", action="store_true", help="Skip cart item seeding")
    parser.add_argument("--skip-low-stock", action="store_true", help="Skip low-stock product creation")
    parser.add_argument("--skip-migrations", action="store_true", help="Skip running migrations (assumes already run)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for product seeding (default: 1000)")
    
    args = parser.parse_args()
    
    print("🚀 Starting Data Seeding Process...")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Products: {args.products:,}")
    print(f"  Users: {args.users:,}")
    print(f"  Items per user: {args.items_per_user}")
    print(f"  Batch size: {args.batch_size:,}")
    print("=" * 60)
    
    # Run migrations first if not skipped
    # Note: Migrations are typically run on API startup, so this is optional
    if not args.skip_migrations:
        print("🔄 Running database migrations...")
        try:
            run_migrations()
            print("✅ Migrations completed")
        except Exception as e:
            print(f"⚠️  Migration warning: {e}")
            print("   Continuing anyway (migrations may already be applied)...")
    
    # Create engine and session
    engine = create_async_engine(
        settings.database_url,
        echo=False
    )
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            
            # Seed products
            await seed_products(session, num_products=args.products, batch_size=args.batch_size)
            
            # Create hot products (for testing)
            await create_hot_products(session, [1, 2, 3, 4, 5, 10, 20, 50, 100, 500])
            
            # Create some low-stock products for concurrency testing
            if not args.skip_low_stock:
                await create_low_stock_products(session, num_products=100)
            
            # Seed cart items
            if not args.skip_cart:
                await seed_cart_items(session, num_users=args.users, items_per_user=args.items_per_user)
            
            # Print statistics
            await print_statistics(session)
            
            print("\n✅ Data seeding completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            sys.exit(1)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
