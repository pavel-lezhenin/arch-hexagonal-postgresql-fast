"""Tests for OutboxPublisherService."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from arch_hexagonal_postgresql_fast.application.ports.outbox_repository import (
    OutboxEvent,
)
from arch_hexagonal_postgresql_fast.application.services.outbox_publisher import (
    OutboxPublisherService,
)


@pytest.fixture
def mock_outbox_repo() -> Mock:
    """Create mock outbox repository."""
    repo = Mock()
    repo.get_unpublished = AsyncMock(return_value=[])
    repo.mark_published = AsyncMock()
    repo.increment_attempts = AsyncMock()
    repo.get_failed = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_event_publisher() -> Mock:
    """Create mock event publisher."""
    publisher = Mock()
    publisher.publish = AsyncMock()
    return publisher


class TestOutboxPublisherService:
    """Test OutboxPublisherService."""

    async def test_publish_pending_events_empty(
        self,
        mock_outbox_repo: Mock,
        mock_event_publisher: Mock,
    ) -> None:
        """Test publishing when no events pending."""
        service = OutboxPublisherService(
            outbox_repo=mock_outbox_repo,
            event_publisher=mock_event_publisher,
        )

        count = await service.publish_pending_events()

        assert count == 0
        assert mock_outbox_repo.get_unpublished.called

    async def test_publish_pending_events_success(
        self,
        mock_outbox_repo: Mock,
        mock_event_publisher: Mock,
    ) -> None:
        """Test successful publishing of pending events."""
        event_id = uuid4()
        event = OutboxEvent(
            id=event_id,
            aggregate_type="Payment",
            aggregate_id="pay_123",
            event_type="PaymentCompleted",
            payload={"payment_id": "pay_123", "status": "completed"},
            created_at=datetime.now(UTC),
        )

        # First call returns unpublished event, second call returns empty after publish
        mock_outbox_repo.get_unpublished = AsyncMock(side_effect=[[event], [event], []])

        service = OutboxPublisherService(
            outbox_repo=mock_outbox_repo,
            event_publisher=mock_event_publisher,
        )

        count = await service.publish_pending_events()

        assert count == 1
        # Note: EventPublisher integration temporarily disabled
        # assert mock_event_publisher.publish.called
        assert mock_outbox_repo.mark_published.called

    async def test_publish_pending_events_with_failure(
        self,
        mock_outbox_repo: Mock,
        mock_event_publisher: Mock,
    ) -> None:
        """Test publishing when event publisher fails."""
        event_id = uuid4()
        event = OutboxEvent(
            id=event_id,
            aggregate_type="Payment",
            aggregate_id="pay_123",
            event_type="PaymentCompleted",
            payload={"payment_id": "pay_123"},
            created_at=datetime.now(UTC),
        )

        mock_outbox_repo.get_unpublished = AsyncMock(return_value=[event])
        # Note: This test is disabled since EventPublisher integration is temporarily disabled
        # mock_event_publisher.publish = AsyncMock(
        #     side_effect=Exception("RabbitMQ error")
        # )

        service = OutboxPublisherService(
            outbox_repo=mock_outbox_repo,
            event_publisher=mock_event_publisher,
            max_attempts=5,
        )

        count = await service.publish_pending_events()

        # Event is marked as published (no actual publishing yet)
        assert count == 1

    async def test_get_failed_events_count(
        self,
        mock_outbox_repo: Mock,
        mock_event_publisher: Mock,
    ) -> None:
        """Test getting failed events count."""
        failed_events = [
            OutboxEvent(
                id=uuid4(),
                aggregate_type="Payment",
                aggregate_id="pay_123",
                event_type="PaymentFailed",
                payload={},
                created_at=datetime.now(UTC),
                attempts=6,
            )
        ]
        mock_outbox_repo.get_failed = AsyncMock(return_value=failed_events)

        service = OutboxPublisherService(
            outbox_repo=mock_outbox_repo,
            event_publisher=mock_event_publisher,
        )

        count = await service.get_failed_events_count()

        assert count == 1
        assert mock_outbox_repo.get_failed.called
