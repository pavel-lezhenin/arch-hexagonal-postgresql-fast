"""Client implementation for arch-hexagonal-postgresql-fast."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from types import TracebackType


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration from environment variables."""

    api_base_url: str = "https://api.example.com"
    api_timeout: float = 30.0

    model_config = {"env_prefix": "ARCH_HEXAGONAL_POSTGRESQL_FAST_"}


class Response(BaseModel):
    """Standard API response model."""

    status: str
    data: dict[str, Any]


class Client:
    """HTTP API client with type safety."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: API base URL. Defaults to env variable.
            timeout: Request timeout in seconds.
        """
        settings = Settings()
        self._base_url = (base_url or settings.api_base_url).rstrip("/")
        self._timeout = timeout or settings.api_timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Client:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def get(self, endpoint: str) -> Response:
        """Perform GET request.

        Args:
            endpoint: API endpoint path.

        Returns:
            Parsed API response.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if not self._client:
            msg = "Client not initialized. Use async context manager."
            raise RuntimeError(msg)

        logger.debug("GET %s", endpoint)
        response = await self._client.get(endpoint)
        response.raise_for_status()

        return Response(status="ok", data=response.json())
