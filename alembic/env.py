"""
Alembic environment configuration for async SQLAlchemy
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import your models and settings
from app.db import Base
from app.settings import settings
from app.models import Product, CartItem  # Import all models for autogenerate

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    try:
        # Check if we're already in an async context
        loop = asyncio.get_running_loop()
        # If we are, we need to run the migrations synchronously
        # by creating a new event loop in a thread or using sync approach
        # For now, we'll use a workaround with nest_asyncio
        try:
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.run(run_async_migrations())
        except ImportError:
            # If nest_asyncio is not available, we need to run it differently
            # Create a new event loop in a thread
            import threading
            import queue
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def run_in_thread():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(run_async_migrations())
                    new_loop.close()
                    result_queue.put(True)
                except Exception as e:
                    exception_queue.put(e)
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if not exception_queue.empty():
                raise exception_queue.get()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
