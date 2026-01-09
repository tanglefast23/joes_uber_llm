"""Anthropic provider implementation."""

import logging
from typing import Any

from anthropic import Anthropic, APIError

from joes_uber_llm.config import PROVIDER_MODELS
from joes_uber_llm.providers.base import BaseProvider, Message

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic API provider for Claude models."""

    @property
    def name(self) -> str:
        """Return the provider name.

        Returns:
            Provider identifier string.
        """
        return "anthropic"

    @property
    def available_models(self) -> list[str]:
        """Return list of available Anthropic models.

        Returns:
            List of supported Claude model identifiers.
        """
        return PROVIDER_MODELS["anthropic"]

    async def chat(
        self,
        messages: list[Message],
        model: str,
        api_key: str,
    ) -> str:
        """Send a chat request to Anthropic API.

        Args:
            messages: List of conversation messages.
            model: Claude model identifier to use.
            api_key: Anthropic API key.

        Returns:
            The assistant's response text.

        Raises:
            ValueError: If the model is not supported.
            RuntimeError: If the API request fails.
        """
        if model not in self.available_models:
            err_msg = f"Model '{model}' not supported. Use: {self.available_models}"
            raise ValueError(err_msg)

        client = Anthropic(api_key=api_key)

        # Anthropic requires system message separate and user/assistant alternating
        system_content = ""
        anthropic_messages: list[dict[str, str]] = []

        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                anthropic_messages.append({"role": msg.role, "content": msg.content})

        try:
            # Build request kwargs
            request_kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": 4096,
                "messages": anthropic_messages,
            }
            if system_content:
                request_kwargs["system"] = system_content

            response = client.messages.create(**request_kwargs)
            if response.content and len(response.content) > 0:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    return str(first_block.text)
            raise RuntimeError("Anthropic returned empty response")
        except APIError as e:
            logger.error("Anthropic API error: %s", e)
            raise RuntimeError(f"Anthropic API error: {e}") from e
