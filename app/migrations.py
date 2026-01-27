"""
Database migration utilities

TEACHING PURPOSE: Demonstrates proper database migration management
"""
import os
import asyncio
import threading
from pathlib import Path
from alembic.config import Config
from alembic import command
from app.settings import settings


def run_migrations():
    """
    Run database migrations using Alembic.
    Can be called from async or sync contexts.
    Handles nested event loops by running in a separate thread if needed.
    """
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context - run migrations in a separate thread
        # This avoids issues with uvloop and nest_asyncio
        result = [None]
        exception = [None]
        
        def run_in_thread():
            try:
                _run_migrations_sync()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()
        
        if exception[0]:
            raise exception[0]
    except RuntimeError:
        # No event loop running, safe to run directly
        _run_migrations_sync()


def _run_migrations_sync():
    """Internal function to run migrations synchronously"""
    # Get the project root directory (where alembic.ini is located)
    # This works whether running from app/ or project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # Go up from app/migrations.py to project root
    alembic_ini_path = project_root / "alembic.ini"
    
    # Change to project root directory so relative paths in alembic.ini work
    original_cwd = os.getcwd()
    try:
        os.chdir(str(project_root))
        
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
