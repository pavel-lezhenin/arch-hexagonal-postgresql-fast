"""Pytest configuration and fixtures for unit tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def base_url() -> str:
    """Provide test base URL."""
    return "https://api.example.com"
