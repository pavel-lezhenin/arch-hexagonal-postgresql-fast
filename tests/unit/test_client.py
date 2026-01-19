"""Tests for client module."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from arch_hexagonal_postgresql_fast.client import Client, Response, Settings


class TestSettings:
    """Tests for Settings."""

    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()

        assert settings.api_base_url == "https://api.example.com"
        assert settings.api_timeout == 30.0


class TestResponse:
    """Tests for Response model."""

    def test_create_response(self):
        """Test creating a response."""
        response = Response(status="ok", data={"key": "value"})

        assert response.status == "ok"
        assert response.data == {"key": "value"}


class TestClient:
    """Tests for Client."""

    def test_init_defaults(self):
        """Test client initialization with defaults."""
        client = Client()

        assert client._base_url == "https://api.example.com"
        assert client._timeout == 30.0

    def test_init_custom_values(self):
        """Test client initialization with custom values."""
        client = Client("https://custom.api.com/", timeout=60.0)

        assert client._base_url == "https://custom.api.com"
        assert client._timeout == 60.0

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped."""
        client = Client("https://api.example.com/")

        assert client._base_url == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with Client() as client:
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_get_success(self, httpx_mock: HTTPXMock):
        """Test successful GET request."""
        httpx_mock.add_response(
            url="https://api.example.com/test",
            json={"result": "success"},
        )

        async with Client() as client:
            response = await client.get("/test")

        assert response.status == "ok"
        assert response.data == {"result": "success"}

    @pytest.mark.asyncio
    async def test_get_without_context_manager_raises(self):
        """Test that GET without context manager raises error."""
        client = Client()

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.get("/test")
