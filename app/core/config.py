import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Mini-CRM"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Настройки основных хранилищ
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/crm_db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-default-secret-key-change-in-production-make-it-very-long-and-secure"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # Тестовые настройки
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://test_user:test_password@localhost:5433/test_crm_db",
    )
    TEST_REDIS_URL: str = os.getenv("TEST_REDIS_URL", "redis://localhost:6380")

    @property
    def database_url(self) -> str:
        return self.TEST_DATABASE_URL if self.TESTING else self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return self.TEST_REDIS_URL if self.TESTING else self.REDIS_URL

    model_config = ConfigDict(env_file=".env")


settings = Settings()
