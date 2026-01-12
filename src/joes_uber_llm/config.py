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
    "openai": [
        "gpt-5.2",
        "gpt-5.2-instant",
        "gpt-5.2-thinking",
        "gpt-5.2-pro",
        "o3",
        "o3-mini",
        "o1",
        "o1-mini",
        "gpt-4o",
        "gpt-4o-mini",
    ],
    "anthropic": [
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
    ],
    "google": [
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ],
    "grok": [
        "grok-3",
        "grok-3-fast",
        "grok-3-mini",
        "grok-3-mini-fast",
        "grok-2-1212",
        "grok-2-vision-1212",
    ],
}

# Default model per provider
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-5.2",
    "anthropic": "claude-sonnet-4-5-20250929",
    "google": "gemini-2.0-flash",
    "grok": "grok-3",
}


settings = Settings()
