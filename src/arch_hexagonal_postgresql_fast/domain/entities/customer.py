"""Customer entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Customer:
    """Customer entity."""

    id: str
    email: str
    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate customer data."""
        if not self.id:
            raise ValueError("Customer ID is required")
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
        if not self.name:
            raise ValueError("Customer name is required")
