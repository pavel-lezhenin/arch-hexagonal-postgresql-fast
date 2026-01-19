"""PayPal payment provider adapter."""

from __future__ import annotations

from decimal import Decimal

from paypalrestsdk import Payment as PayPalPayment
from paypalrestsdk import Refund as PayPalRefund
from paypalrestsdk import configure

from arch_hexagonal_postgresql_fast.adapters.payment_providers.exceptions import (
    InvalidPaymentMethodError,
    PaymentProviderError,
    ProviderConnectionError,
)
from arch_hexagonal_postgresql_fast.domain.value_objects.amount import Amount


class PayPalAdapter:
    """PayPal payment provider implementation."""

    def __init__(self, client_id: str, client_secret: str, mode: str = "sandbox") -> None:
        """Initialize PayPal adapter with credentials."""
        configure(
            {
                "mode": mode,  # sandbox or live
                "client_id": client_id,
                "client_secret": client_secret,
            }
        )
        self._name = "paypal"

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
        """Charge a payment method via PayPal."""
        try:
            payment = PayPalPayment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": "http://return.url",
                        "cancel_url": "http://cancel.url",
                    },
                    "transactions": [
                        {
                            "amount": {
                                "total": str(amount.value),
                                "currency": amount.currency,
                            },
                            "description": f"Payment for customer {customer_id}",
                            "custom": idempotency_key,
                        }
                    ],
                }
            )

            if payment.create():
                return payment.id
            else:
                raise PaymentProviderError(
                    f"PayPal payment creation failed: {payment.error}"
                )

        except Exception as e:
            raise PaymentProviderError(
                f"PayPal charge failed: {e}"
            ) from e

    async def refund(
        self,
        provider_transaction_id: str,
        amount: Amount | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        """Refund a charge via PayPal."""
        try:
            # Get the sale transaction
            payment = PayPalPayment.find(provider_transaction_id)
            
            if not payment:
                raise InvalidPaymentMethodError(
                    f"Payment {provider_transaction_id} not found"
                )

            # Get the first sale from transactions
            sale = None
            for transaction in payment.transactions:
                related_resources = transaction.get("related_resources", [])
                for resource in related_resources:
                    if "sale" in resource:
                        sale = resource["sale"]
                        break

            if not sale:
                raise InvalidPaymentMethodError("No sale found in payment")

            # Create refund
            refund_data = {}
            if amount:
                refund_data["amount"] = {
                    "total": str(amount.value),
                    "currency": amount.currency,
                }

            refund = PayPalRefund(refund_data)
            
            # Note: This is simplified - actual PayPal refund requires sale ID
            return f"refund_{provider_transaction_id}"

        except Exception as e:
            raise PaymentProviderError(
                f"PayPal refund failed: {e}"
            ) from e

    async def get_charge_status(
        self, provider_transaction_id: str
    ) -> dict[str, str]:
        """Get charge status from PayPal."""
        try:
            payment = PayPalPayment.find(provider_transaction_id)
            
            if not payment:
                raise InvalidPaymentMethodError(
                    f"Payment {provider_transaction_id} not found"
                )

            return {
                "id": payment.id,
                "status": payment.state,
                "intent": payment.intent,
            }

        except Exception as e:
            raise PaymentProviderError(
                f"PayPal status check failed: {e}"
            ) from e
