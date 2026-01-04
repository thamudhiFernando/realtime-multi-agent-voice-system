"""
Configuration management for ElectroMart Multi-Agent System
"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"

    # Database Configuration
    database_url: str = "sqlite:///./data/electromart.db"  # Default to SQLite for easy setup
    redis_url: str = "redis://localhost:6379/0"

    # LangSmith Configuration
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "electromart-agents"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # Server Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Security
    jwt_secret: str = "change-this-secret-key"
    cors_origins: str = "http://localhost:3000"

    # Application Settings
    log_level: str = "INFO"
    environment: str = "development"

    # Vector Store
    chroma_persist_directory: str = "./data/chroma"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
