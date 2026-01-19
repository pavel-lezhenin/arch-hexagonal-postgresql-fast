"""Services package."""

from __future__ import annotations

from .outbox_publisher import OutboxPublisherService

__all__ = ["OutboxPublisherService"]
