"""Application configuration settings."""

import os
import secrets
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_hex(32))
    )


# Available models per provider
PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-3-5-haiku-20241022",
        "claude-opus-4-20250514",
    ],
    "google": ["gemini-2.0-flash-exp", "gemini-1.5-flash-002", "gemini-1.5-pro-002"],
}

# Default model per provider
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.0-flash-exp",
}


settings = Settings()
