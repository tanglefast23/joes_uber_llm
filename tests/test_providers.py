"""Tests for LLM provider implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from joes_uber_llm.providers import AnthropicProvider, GoogleProvider, OpenAIProvider
from joes_uber_llm.providers.base import Message


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_name(self) -> None:
        """Test provider name property."""
        provider = OpenAIProvider()
        assert provider.name == "openai"

    def test_available_models(self) -> None:
        """Test available models list."""
        provider = OpenAIProvider()
        models = provider.available_models
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models

    @pytest.mark.asyncio
    async def test_chat_invalid_model(self) -> None:
        """Test that invalid model raises ValueError."""
        provider = OpenAIProvider()
        messages = [Message(role="user", content="Hello")]

        with pytest.raises(ValueError, match="not supported"):
            await provider.chat(messages, "invalid-model", "test-key")

    @pytest.mark.asyncio
    async def test_chat_success(self) -> None:
        """Test successful chat completion."""
        provider = OpenAIProvider()
        messages = [Message(role="user", content="Hello")]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"

        with patch("joes_uber_llm.providers.openai.AsyncOpenAI") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            result = await provider.chat(messages, "gpt-4o-mini", "test-key")

            assert result == "Hello! How can I help you?"


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_name(self) -> None:
        """Test provider name property."""
        provider = AnthropicProvider()
        assert provider.name == "anthropic"

    def test_available_models(self) -> None:
        """Test available models list."""
        provider = AnthropicProvider()
        models = provider.available_models
        assert "claude-sonnet-4-20250514" in models

    @pytest.mark.asyncio
    async def test_chat_invalid_model(self) -> None:
        """Test that invalid model raises ValueError."""
        provider = AnthropicProvider()
        messages = [Message(role="user", content="Hello")]

        with pytest.raises(ValueError, match="not supported"):
            await provider.chat(messages, "invalid-model", "test-key")

    @pytest.mark.asyncio
    async def test_chat_success(self) -> None:
        """Test successful chat completion."""
        provider = AnthropicProvider()
        messages = [Message(role="user", content="Hello")]

        mock_text_block = MagicMock()
        mock_text_block.text = "Hello! How can I help you?"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        with patch("joes_uber_llm.providers.anthropic.Anthropic") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.messages.create.return_value = mock_response

            result = await provider.chat(
                messages, "claude-sonnet-4-20250514", "test-key"
            )

            assert result == "Hello! How can I help you?"


class TestGoogleProvider:
    """Tests for Google Gemini provider."""

    def test_name(self) -> None:
        """Test provider name property."""
        provider = GoogleProvider()
        assert provider.name == "google"

    def test_available_models(self) -> None:
        """Test available models list."""
        provider = GoogleProvider()
        models = provider.available_models
        assert "gemini-1.5-flash-002" in models

    @pytest.mark.asyncio
    async def test_chat_invalid_model(self) -> None:
        """Test that invalid model raises ValueError."""
        provider = GoogleProvider()
        messages = [Message(role="user", content="Hello")]

        with pytest.raises(ValueError, match="not supported"):
            await provider.chat(messages, "invalid-model", "test-key")

    @pytest.mark.asyncio
    async def test_chat_success(self) -> None:
        """Test successful chat completion."""
        provider = GoogleProvider()
        messages = [Message(role="user", content="Hello")]

        mock_response = MagicMock()
        mock_response.text = "Hello! How can I help you?"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("joes_uber_llm.providers.google.genai.Client") as mock_client_cls:
            mock_client_cls.return_value = mock_client

            result = await provider.chat(messages, "gemini-1.5-flash-002", "test-key")

            assert result == "Hello! How can I help you?"
