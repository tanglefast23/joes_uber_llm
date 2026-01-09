"""Google Gemini provider implementation."""

import logging

from google import genai
from google.genai import errors, types

from joes_uber_llm.config import PROVIDER_MODELS
from joes_uber_llm.providers.base import BaseProvider, Message

logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    """Google Generative AI provider for Gemini models."""

    @property
    def name(self) -> str:
        """Return the provider name.

        Returns:
            Provider identifier string.
        """
        return "google"

    @property
    def available_models(self) -> list[str]:
        """Return list of available Google models.

        Returns:
            List of supported Gemini model identifiers.
        """
        return PROVIDER_MODELS["google"]

    async def chat(
        self,
        messages: list[Message],
        model: str,
        api_key: str,
    ) -> str:
        """Send a chat request to Google Gemini API.

        Args:
            messages: List of conversation messages.
            model: Gemini model identifier to use.
            api_key: Google API key.

        Returns:
            The assistant's response text.

        Raises:
            ValueError: If the model is not supported.
            RuntimeError: If the API request fails.
        """
        if model not in self.available_models:
            err_msg = f"Model '{model}' not supported. Use: {self.available_models}"
            raise ValueError(err_msg)

        client = genai.Client(api_key=api_key)

        # Convert messages to Gemini format
        contents: list[types.Content] = []
        system_instruction = ""

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append(
                    types.Content(role="user", parts=[types.Part(text=msg.content)])
                )
            elif msg.role == "assistant":
                contents.append(
                    types.Content(role="model", parts=[types.Part(text=msg.content)])
                )

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction if system_instruction else None,
            )

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            if response.text:
                return response.text
            raise RuntimeError("Google Gemini returned empty response")
        except errors.APIError as e:
            logger.error("Google API error: %s", e)
            raise RuntimeError(f"Google API error: {e}") from e
