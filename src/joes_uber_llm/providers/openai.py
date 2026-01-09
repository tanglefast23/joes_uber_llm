"""OpenAI provider implementation."""

import logging

from openai import AsyncOpenAI, OpenAIError

from joes_uber_llm.config import PROVIDER_MODELS
from joes_uber_llm.providers.base import BaseProvider, Message

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider for GPT models."""

    @property
    def name(self) -> str:
        """Return the provider name.

        Returns:
            Provider identifier string.
        """
        return "openai"

    @property
    def available_models(self) -> list[str]:
        """Return list of available OpenAI models.

        Returns:
            List of supported GPT model identifiers.
        """
        return PROVIDER_MODELS["openai"]

    async def chat(
        self,
        messages: list[Message],
        model: str,
        api_key: str,
    ) -> str:
        """Send a chat request to OpenAI API.

        Args:
            messages: List of conversation messages.
            model: GPT model identifier to use.
            api_key: OpenAI API key.

        Returns:
            The assistant's response text.

        Raises:
            ValueError: If the model is not supported.
            RuntimeError: If the API request fails.
        """
        if model not in self.available_models:
            msg = f"Model '{model}' not supported. Use: {self.available_models}"
            raise ValueError(msg)

        client = AsyncOpenAI(api_key=api_key)

        openai_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=openai_messages,  # type: ignore[arg-type]
            )
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("OpenAI returned empty response")
            return content
        except OpenAIError as e:
            logger.error("OpenAI API error: %s", e)
            raise RuntimeError(f"OpenAI API error: {e}") from e
