"""
Application configuration using pydantic-settings.
Loads values from .env file at the project root.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    GOOGLE_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"

    # --- SMTP / Email ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = "finance@yourcompany.com"
    SENDER_NAME: str = "Finance Team"

    # --- App ---
    DRY_RUN_MODE: bool = True
    DB_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "finance_agent.db",
    )
    PAYMENT_LINK_BASE: str = "https://pay.yourcompany.com"

    # --- Security ---
    API_SECRET_KEY: str = "change_this_to_a_random_secret"

    class Config:
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            ".env",
        )
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
