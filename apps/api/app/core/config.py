"""Read local settings from environment variables and the root .env file."""

from decimal import Decimal
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    database_url: str = "postgresql+psycopg:///shopguard"
    jwt_secret_key: str = "local-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    shop_tax_rate: Decimal = Decimal("0.08")
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    ai_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-6.2-astra"

    @model_validator(mode="after")
    def check_ai_provider(self) -> "Settings":
        if self.ai_provider not in {"mock", "openai"}:
            raise ValueError("AI_PROVIDER must be 'mock' or 'openai'.")
        if self.ai_provider == "openai" and not self.openai_api_key:
            raise ValueError("Set OPENAI_API_KEY in the private .env to use the OpenAI provider.")
        return self

    @model_validator(mode="after")
    def check_production_secret(self) -> "Settings":
        if self.app_env == "production" and self.jwt_secret_key == "local-only-change-me":
            raise ValueError("Set JWT_SECRET_KEY to a private value in production.")
        if not Decimal("0") <= self.shop_tax_rate <= Decimal("1"):
            raise ValueError("SHOP_TAX_RATE must be between 0 and 1.")
        return self


settings = Settings()
