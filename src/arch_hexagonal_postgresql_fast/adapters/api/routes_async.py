"""Async API routes for command-based processing."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from arch_hexagonal_postgresql_fast.application.commands import (
    ProcessPaymentCommand,
)
from arch_hexagonal_postgresql_fast.application.ports.command_publisher import (
    CommandPublisher,
)
from arch_hexagonal_postgresql_fast.feature_flags import FeatureFlags

router = APIRouter(prefix="/v2", tags=["payments-v2"])


class AsyncPaymentRequest(BaseModel):
    """Request schema for async payment processing."""

    customer_id: str = Field(..., description="Customer identifier")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code")
    payment_method: str = Field(..., description="Payment method type")
    payment_method_token: str = Field(..., description="Payment method token")
    idempotency_key: str = Field(..., description="Idempotency key for deduplication")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")


class AsyncPaymentResponse(BaseModel):
    """Response schema for async payment processing."""

    status: str = Field(..., description="Processing status")
    command_id: str = Field(..., description="Command identifier")
    payment_id: str = Field(..., description="Payment identifier (same as command_id)")
    message: str = Field(..., description="Status message")


@router.post(
    "/payments",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AsyncPaymentResponse,
)
async def create_payment_async(
    request: AsyncPaymentRequest,
    command_publisher: CommandPublisher = Depends(),
) -> AsyncPaymentResponse:
    """Create payment asynchronously via command queue.

    Returns 202 Accepted immediately. Payment processing happens in background worker.
    Use GET /v2/payments/{payment_id} to check status.

    Args:
        request: Payment request data
        command_publisher: Command publisher dependency

    Returns:
        Response with command_id for status polling

    """
    if not FeatureFlags.ENABLE_ASYNC_COMMANDS:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Async processing is not enabled. Use /v1/payments endpoint.",
        )

    # Create command
    command_id = str(uuid.uuid4())
    command = ProcessPaymentCommand(
        command_id=command_id,
        idempotency_key=request.idempotency_key,
        timestamp=datetime.now(UTC),
        customer_id=request.customer_id,
        amount=request.amount,
        currency=request.currency,
        payment_method=request.payment_method,
        payment_method_token=request.payment_method_token,
        metadata=request.metadata,
    )

    # Publish command to queue
    await command_publisher.publish_process_payment(command)

    return AsyncPaymentResponse(
        status="accepted",
        command_id=command_id,
        payment_id=command_id,
        message="Payment is being processed asynchronously. Use GET /v2/payments/{payment_id} to check status.",
    )


@router.get("/payments/{payment_id}", response_model=dict[str, str])
async def get_payment_status(payment_id: str) -> dict[str, str]:
    """Get payment status by ID.

    Args:
        payment_id: Payment identifier

    Returns:
        Payment status information

    """
    # TODO: Implement payment status query
    # For now, return placeholder
    return {
        "payment_id": payment_id,
        "status": "processing",
        "message": "Status polling not yet implemented. Check database directly.",
    }
