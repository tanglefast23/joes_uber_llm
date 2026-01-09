"""Tests for API routes."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestPagesRoutes:
    """Tests for page rendering routes."""

    @pytest.mark.asyncio
    async def test_index_page(self, client: AsyncClient) -> None:
        """Test that index page renders successfully."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "Joe's Uber LLM" in response.text
        assert "openai" in response.text.lower()
        assert "anthropic" in response.text.lower()


class TestChatRoutes:
    """Tests for chat API routes."""

    @pytest.mark.asyncio
    async def test_chat_missing_api_key(self, client: AsyncClient) -> None:
        """Test that chat endpoint requires API key."""
        response = await client.post(
            "/api/chat",
            data={
                "message": "Hello",
                "provider": "openai",
                "model": "gpt-4o-mini",
            },
        )

        assert response.status_code == 400
        assert "API key required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_invalid_provider(self, client: AsyncClient) -> None:
        """Test that chat endpoint validates provider."""
        response = await client.post(
            "/api/chat",
            data={
                "message": "Hello",
                "provider": "invalid",
                "model": "some-model",
            },
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_invalid_model(self, client: AsyncClient) -> None:
        """Test that chat endpoint validates model."""
        response = await client.post(
            "/api/chat",
            data={
                "message": "Hello",
                "provider": "openai",
                "model": "invalid-model",
            },
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 400
        assert "Invalid model" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_success(self, client: AsyncClient) -> None:
        """Test successful chat request."""
        with patch("joes_uber_llm.routes.chat.PROVIDERS") as mock_providers:
            mock_provider = AsyncMock()
            mock_provider.chat.return_value = "Hello! How can I help?"
            mock_providers.__getitem__.return_value = mock_provider
            mock_providers.__contains__.return_value = True

            response = await client.post(
                "/api/chat",
                data={
                    "message": "Hello",
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 200
            assert "Hello" in response.text

    @pytest.mark.asyncio
    async def test_clear_conversation(self, client: AsyncClient) -> None:
        """Test clearing conversation history."""
        response = await client.post(
            "/api/clear",
            headers={"X-Session-ID": "test-session"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_models(self, client: AsyncClient) -> None:
        """Test getting models for a provider."""
        response = await client.get("/api/models/openai")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "gpt-4o" in data["models"]

    @pytest.mark.asyncio
    async def test_get_models_invalid_provider(self, client: AsyncClient) -> None:
        """Test getting models for invalid provider."""
        response = await client.get("/api/models/invalid")

        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]
