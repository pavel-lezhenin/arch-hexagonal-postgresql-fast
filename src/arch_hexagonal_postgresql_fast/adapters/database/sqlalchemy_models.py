"""SQLAlchemy models for PostgreSQL."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Numeric, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models."""

    pass


class PaymentModel(Base):
    """Payment table model."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(255), index=True)
    amount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount_currency: Mapped[str] = mapped_column(String(3))
    payment_method: Mapped[str] = mapped_column(String(50))
    provider: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), index=True)
    provider_transaction_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    refunded_amount_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    refunded_amount_currency: Mapped[str] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    metadata: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict
    )


class TransactionModel(Base):
    """Transaction table model."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payment_id: Mapped[str] = mapped_column(
        String(36), index=True
    )
    amount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount_currency: Mapped[str] = mapped_column(String(3))
    transaction_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50))
    provider: Mapped[str] = mapped_column(String(50))
    provider_transaction_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    metadata: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict
    )


class CustomerModel(Base):
    """Customer table model."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    metadata: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict
    )
