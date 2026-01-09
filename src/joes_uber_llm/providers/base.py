"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    """A chat message with role and content."""

    role: str
    content: str


class BaseProvider(ABC):
    """Abstract base class for LLM provider implementations.

    All LLM providers must implement this interface to ensure
    consistent behavior across different APIs.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name.

        Returns:
            Provider identifier string (e.g., 'openai', 'anthropic').
        """

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """Return list of available model identifiers.

        Returns:
            List of model ID strings supported by this provider.
        """

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str,
        api_key: str,
    ) -> str:
        """Send a chat request and return the response.

        Args:
            messages: List of conversation messages.
            model: Model identifier to use.
            api_key: API key for authentication.

        Returns:
            The assistant's response text.

        Raises:
            ValueError: If the model is not supported.
            RuntimeError: If the API request fails.
        """
