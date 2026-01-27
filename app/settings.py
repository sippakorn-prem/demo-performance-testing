"""
Application settings and configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database (defaults to docker-compose setup, override with DATABASE_URL env var)
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/demo_db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
