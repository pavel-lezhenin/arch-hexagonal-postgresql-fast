"""Stripe payment provider adapter."""

from __future__ import annotations

import stripe

from arch_hexagonal_postgresql_fast.adapters.payment_providers.exceptions import (
    InsufficientFundsError,
    InvalidPaymentMethodError,
    PaymentProviderError,
    ProviderConnectionError,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount


class StripeAdapter:
    """Stripe payment provider implementation."""

    def __init__(self, api_key: str) -> None:
        """Initialize Stripe adapter with API key."""
        stripe.api_key = api_key
        self._name = "stripe"

    @property
    def name(self) -> str:
        """Provider name."""
        return self._name

    async def charge(
        self,
        amount: Amount,
        payment_method_token: str,
        idempotency_key: str,
        customer_id: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Charge a payment method via Stripe."""
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount.to_cents(),
                currency=amount.currency.lower(),
                payment_method=payment_method_token,
                customer=customer_id,
                confirm=True,
                metadata=metadata or {},
                idempotency_key=idempotency_key,
            )
            return payment_intent["id"]
        except stripe.error.CardError as e:
            # Card was declined
            raise InsufficientFundsError(str(e)) from e
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            raise InvalidPaymentMethodError(str(e)) from e
        except (
            stripe.error.APIConnectionError,
            stripe.error.APIError,
        ) as e:
            # Network or API error
            raise ProviderConnectionError(str(e)) from e
        except Exception as e:
            raise PaymentProviderError(f"Stripe charge failed: {e}") from e

    async def refund(
        self,
        provider_transaction_id: str,
        amount: Amount | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        """Refund a charge via Stripe."""
        try:
            params: dict[str, str | int] = {
                "payment_intent": provider_transaction_id,
            }
            if amount:
                params["amount"] = amount.to_cents()
            if idempotency_key:
                params["idempotency_key"] = idempotency_key

            refund = stripe.Refund.create(**params)  # type: ignore[arg-type]
            return refund["id"]
        except stripe.error.InvalidRequestError as e:
            raise InvalidPaymentMethodError(str(e)) from e
        except (
            stripe.error.APIConnectionError,
            stripe.error.APIError,
        ) as e:
            raise ProviderConnectionError(str(e)) from e
        except Exception as e:
            raise PaymentProviderError(f"Stripe refund failed: {e}") from e

    async def get_charge_status(
        self, provider_transaction_id: str
    ) -> dict[str, str]:
        """Get charge status from Stripe."""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(
                provider_transaction_id
            )
            return {
                "id": payment_intent["id"],
                "status": payment_intent["status"],
                "amount": str(payment_intent["amount"]),
                "currency": payment_intent["currency"],
            }
        except Exception as e:
            raise PaymentProviderError(
                f"Stripe status check failed: {e}"
            ) from e
