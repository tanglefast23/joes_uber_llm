"""Grok (xAI) provider implementation."""

import logging

from openai import AsyncOpenAI, OpenAIError

from joes_uber_llm.config import PROVIDER_MODELS
from joes_uber_llm.providers.base import BaseProvider, Message

logger = logging.getLogger(__name__)

# xAI API base URL (OpenAI-compatible)
XAI_BASE_URL = "https://api.x.ai/v1"


class GrokProvider(BaseProvider):
    """xAI Grok API provider for Grok models.

    Uses OpenAI-compatible API with xAI's base URL.
    """

    @property
    def name(self) -> str:
        """Return the provider name.

        Returns:
            Provider identifier string.
        """
        return "grok"

    @property
    def available_models(self) -> list[str]:
        """Return list of available Grok models.

        Returns:
            List of supported Grok model identifiers.
        """
        return PROVIDER_MODELS["grok"]

    async def chat(
        self,
        messages: list[Message],
        model: str,
        api_key: str,
    ) -> str:
        """Send a chat request to xAI Grok API.

        Args:
            messages: List of conversation messages.
            model: Grok model identifier to use.
            api_key: xAI API key.

        Returns:
            The assistant's response text.

        Raises:
            ValueError: If the model is not supported.
            RuntimeError: If the API request fails.
        """
        if model not in self.available_models:
            msg = f"Model '{model}' not supported. Use: {self.available_models}"
            raise ValueError(msg)

        client = AsyncOpenAI(api_key=api_key, base_url=XAI_BASE_URL)

        openai_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=openai_messages,  # type: ignore[arg-type]
            )
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("Grok returned empty response")
            return content
        except OpenAIError as e:
            logger.error("Grok API error: %s", e)
            raise RuntimeError(f"Grok API error: {e}") from e
