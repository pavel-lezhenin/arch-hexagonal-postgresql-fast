"""Amount value object."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from arch_hexagonal_postgresql_fast.domain.exceptions import InvalidAmountError


@dataclass(frozen=True)
class Amount:
    """Immutable money amount with currency."""

    value: Decimal
    currency: str

    def __post_init__(self) -> None:
        """Validate amount after initialization."""
        if self.value < 0:
            raise InvalidAmountError(f"Amount cannot be negative, got {self.value}")
        if not self.currency or len(self.currency) != 3:
            raise InvalidAmountError(f"Currency must be 3-letter ISO code, got {self.currency}")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value:.2f} {self.currency}"

    def __add__(self, other: Amount) -> Amount:
        """Add two amounts (must be same currency)."""
        if self.currency != other.currency:
            raise InvalidAmountError(
                f"Cannot add amounts with different currencies: {self.currency} != {other.currency}"
            )
        return Amount(value=self.value + other.value, currency=self.currency)

    def __sub__(self, other: Amount) -> Amount:
        """Subtract two amounts (must be same currency)."""
        if self.currency != other.currency:
            raise InvalidAmountError(
                f"Cannot subtract amounts with different currencies: "
                f"{self.currency} != {other.currency}"
            )
        result = self.value - other.value
        # Allow zero but not negative
        if result < 0:
            raise InvalidAmountError(f"Subtraction would result in negative amount: {result}")
        return Amount(value=result, currency=self.currency)

    def to_cents(self) -> int:
        """Convert to cents/smallest currency unit."""
        return int(self.value * 100)

    @classmethod
    def from_cents(cls, cents: int, currency: str) -> Amount:
        """Create amount from cents/smallest currency unit."""
        return cls(value=Decimal(cents) / 100, currency=currency)

    @classmethod
    def zero(cls, currency: str = "USD") -> Amount:
        """Create zero amount (for initial values)."""
        return cls(value=Decimal("0.00"), currency=currency)
