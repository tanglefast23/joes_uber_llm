"""Pytest configuration and fixtures."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from joes_uber_llm.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Create an async HTTP client for testing.

    Yields:
        Configured AsyncClient instance.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
