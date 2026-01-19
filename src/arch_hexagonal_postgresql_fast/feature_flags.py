"""Feature flags for gradual rollout."""

from __future__ import annotations

import logging
import os
from typing import ClassVar

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Feature flags for controlling rollout."""

    # Command-based async processing
    ENABLE_ASYNC_COMMANDS: ClassVar[bool] = (
        os.getenv("ENABLE_ASYNC_COMMANDS", "false").lower() == "true"
    )

    # Outbox pattern for events
    ENABLE_OUTBOX_PATTERN: ClassVar[bool] = (
        os.getenv("ENABLE_OUTBOX_PATTERN", "true").lower() == "true"
    )

    # Retry mechanism
    ENABLE_RETRY_LOGIC: ClassVar[bool] = os.getenv("ENABLE_RETRY_LOGIC", "true").lower() == "true"

    # Compensation for failures
    ENABLE_COMPENSATION: ClassVar[bool] = os.getenv("ENABLE_COMPENSATION", "true").lower() == "true"

    @classmethod
    def log_status(cls) -> None:
        """Log current feature flag status."""
        logger.info("Feature Flags:")
        logger.info("  ENABLE_ASYNC_COMMANDS: %s", cls.ENABLE_ASYNC_COMMANDS)
        logger.info("  ENABLE_OUTBOX_PATTERN: %s", cls.ENABLE_OUTBOX_PATTERN)
        logger.info("  ENABLE_RETRY_LOGIC: %s", cls.ENABLE_RETRY_LOGIC)
        logger.info("  ENABLE_COMPENSATION: %s", cls.ENABLE_COMPENSATION)
