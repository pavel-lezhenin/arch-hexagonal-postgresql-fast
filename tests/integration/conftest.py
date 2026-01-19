"""Pytest configuration and fixtures for integration tests."""

from __future__ import annotations

import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMqContainer
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def postgres_container() -> object:
    """PostgreSQL testcontainer."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def rabbitmq_container() -> object:
    """RabbitMQ testcontainer."""
    with RabbitMqContainer("rabbitmq:3.13-management") as rabbitmq:
        yield rabbitmq


@pytest.fixture(scope="session")
def redis_container() -> object:
    """Redis testcontainer."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


# Add testcontainers fixtures here when needed
# Example:
# from testcontainers.postgres import PostgresContainer
#
# @pytest.fixture(scope="session")
# def postgres_container():
#     """Start PostgreSQL container for integration tests."""
#     with PostgresContainer("postgres:16") as container:
#         yield container
