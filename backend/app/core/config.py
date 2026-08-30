from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, populated from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    PROJECT_NAME: str = "Wholesale Marketplace API"
    API_V1_PREFIX: str = "/api/v1"
    ENV: str = "development"
    DEBUG: bool = True

    # Database — SQLite default for local dev (no services needed)
    # Override with a PostgreSQL URL in .env for production.
    DATABASE_URL: str = "sqlite:///./wholesale.db"

    # Auth
    SECRET_KEY: str = "change-me-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - allow all dev origins (vanilla at 8000/vanilla, 3001, etc.)
    # For production, restrict to specific domains via .env; never include "null".
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8000",
        "http://localhost:8002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:5173",
        # "null" intentionally omitted — it allows file:// origins which is a security risk
    ]

    # Wholesale business settings
    REQUIRE_LOGIN_TO_SEE_PRICES: bool = False  # if True, guests cannot see net/gross prices
    REQUIRE_BUYER_APPROVAL: bool = False  # if True, buyers need admin approval before buying
    ALLOW_CASH_ON_DELIVERY_ONLY: bool = True


settings = Settings()
