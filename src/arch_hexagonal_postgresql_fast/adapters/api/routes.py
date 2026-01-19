"""FastAPI routes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from arch_hexagonal_postgresql_fast.adapters.api.dependencies import (
    get_event_publisher,
    get_idempotency_store,
    get_outbox_repository,
    get_payment_provider,
    get_payment_repository,
    get_transaction_repository,
)
from arch_hexagonal_postgresql_fast.application.ports.event_publisher import (
    EventPublisher,
)
from arch_hexagonal_postgresql_fast.application.ports.idempotency_store import (
    IdempotencyStore,
)
from arch_hexagonal_postgresql_fast.application.ports.outbox_repository import (
    OutboxRepository,
)
from arch_hexagonal_postgresql_fast.application.ports.payment_provider import (
    PaymentProvider,
)
from arch_hexagonal_postgresql_fast.application.ports.payment_repository import (
    PaymentRepository,
)
from arch_hexagonal_postgresql_fast.application.ports.transaction_repository import (
    TransactionRepository,
)
from arch_hexagonal_postgresql_fast.application.use_cases.get_transaction_status import (
    GetTransactionStatus,
    GetTransactionStatusRequest,
)
from arch_hexagonal_postgresql_fast.application.use_cases.process_payment import (
    ProcessPayment,
    ProcessPaymentRequest,
)
from arch_hexagonal_postgresql_fast.application.use_cases.refund_payment import (
    RefundPayment,
    RefundPaymentRequest,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount
from arch_hexagonal_postgresql_fast.domain.value_objects.payment_method import (
    PaymentMethod,
)

router = APIRouter(prefix="/api/v1", tags=["payments"])


class ProcessPaymentSchema(BaseModel):
    """Schema for processing payment."""

    customer_id: str = Field(..., description="Customer identifier")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code")
    payment_method: PaymentMethod = Field(..., description="Payment method type")
    payment_method_token: str = Field(..., description="Payment method token")
    idempotency_key: str = Field(..., description="Idempotency key")
    provider: str = Field(default="stripe", description="Payment provider")
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")


class RefundPaymentSchema(BaseModel):
    """Schema for refunding payment."""

    amount: Decimal | None = Field(None, gt=0, description="Refund amount (None for full)")
    idempotency_key: str | None = Field(None, description="Idempotency key")


@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def process_payment(
    request: ProcessPaymentSchema,
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    provider: PaymentProvider = Depends(get_payment_provider),
    events: EventPublisher = Depends(get_event_publisher),
    idempotency: IdempotencyStore = Depends(get_idempotency_store),
    outbox_repo: OutboxRepository = Depends(get_outbox_repository),
) -> dict[str, str]:
    """Process a payment."""
    try:
        use_case = ProcessPayment(
            payment_repo,
            transaction_repo,
            provider,
            events,
            idempotency,
            outbox_repo,
        )

        result = await use_case.execute(
            ProcessPaymentRequest(
                customer_id=request.customer_id,
                amount=Amount(value=request.amount, currency=request.currency),
                payment_method=request.payment_method,
                payment_method_token=request.payment_method_token,
                idempotency_key=request.idempotency_key,
                metadata=request.metadata,
            )
        )

        return {
            "payment_id": result.payment_id,
            "status": result.status,
            "provider_transaction_id": result.provider_transaction_id or "",
            "created_at": result.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/payments/{payment_id}/refund")
async def refund_payment(
    payment_id: str,
    request: RefundPaymentSchema,
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    provider: PaymentProvider = Depends(get_payment_provider),
    events: EventPublisher = Depends(get_event_publisher),
    idempotency: IdempotencyStore = Depends(get_idempotency_store),
) -> dict[str, str]:
    """Refund a payment."""
    try:
        use_case = RefundPayment(payment_repo, transaction_repo, provider, events, idempotency)

        # Get payment to determine currency
        payment = await payment_repo.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found",
            )

        refund_amount = None
        if request.amount:
            refund_amount = Amount(
                value=request.amount,
                currency=payment.amount.currency,
            )

        result = await use_case.execute(
            RefundPaymentRequest(
                payment_id=payment_id,
                amount=refund_amount,
                idempotency_key=request.idempotency_key,
            )
        )

        return {
            "payment_id": result.payment_id,
            "refund_amount": result.refund_amount,
            "status": result.status,
            "refund_transaction_id": result.refund_transaction_id,
            "created_at": result.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/payments/{payment_id}")
async def get_payment_status(
    payment_id: str,
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
) -> dict[str, object]:
    """Get payment status."""
    try:
        use_case = GetTransactionStatus(payment_repo, transaction_repo)

        result = await use_case.execute(GetTransactionStatusRequest(payment_id=payment_id))

        return {
            "payment_id": result.payment_id,
            "customer_id": result.customer_id,
            "total_amount": result.total_amount,
            "refunded_amount": result.refunded_amount,
            "status": result.status,
            "transactions": [
                {
                    "id": tx.id,
                    "type": tx.type,
                    "amount": tx.amount,
                    "status": tx.status,
                    "provider_transaction_id": tx.provider_transaction_id,
                    "created_at": tx.created_at.isoformat(),
                }
                for tx in result.transactions
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
