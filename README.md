# arch-hexagonal-postgresql-fast

**Event-Driven Hexagonal Payment Service** — production-ready payment processing with transactional outbox pattern, built on FastAPI + PostgreSQL + RabbitMQ.

## 🎯 Project Goal

Reference implementation of **Event-Driven Hexagonal Architecture** for a payment service with guaranteed event delivery and transaction atomicity.

### What This Is and Why

| Problem | Solution |
|---------|----------|
| Event loss during failures | **Transactional Outbox** — events saved to DB together with payment |
| Duplicate payments | **Idempotency Keys** via Redis |
| Provider lock-in | **Ports & Adapters** — easily add Stripe/PayPal/Adyen |
| Testing complexity | **MockStripeAdapter** — tests without real APIs |
| Data inconsistency | **Exactly-once delivery** via outbox worker |

### Key Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                    Event-Driven Flow                            │
│                                                                 │
│  POST /payments ──► UseCase ──► PostgreSQL (Payment + Outbox)  │
│                                        │                        │
│                         OutboxWorker ◄─┘                        │
│                              │                                  │
│                              ▼                                  │
│                         RabbitMQ ──► Consumers (Analytics, etc) │
└─────────────────────────────────────────────────────────────────┘
```

**Transactional Outbox Pattern:**
- Payment and event saved in single transaction
- Background worker publishes events to RabbitMQ
- On failure — automatic retry with exponential backoff
- Guarantee: events won't be lost even if service crashes

## 💡 Business Value & Use Case

This project demonstrates a **production-ready payment processing microservice** that handles real-world challenges:

### What We Built

A payment service that:
- **Processes payments** across multiple providers (Stripe, PayPal) with unified interface
- **Prevents duplicate charges** through Redis-based idempotency keys
- **Maintains transactional integrity** using PostgreSQL ACID guarantees
- **Publishes lifecycle events** to RabbitMQ for downstream systems (analytics, notifications)
- **Supports partial/full refunds** with domain-driven business rules
- **Provides audit trail** through immutable transaction records

### Business Benefits

1. **🔌 Provider Independence**: Easily switch or add payment providers without changing business logic
2. **💰 Revenue Protection**: Idempotency prevents double-charging customers during network failures
3. **📊 Observability**: Structured logging + event stream enables real-time analytics and alerting
4. **🔒 Data Integrity**: PostgreSQL transactions ensure payments and refunds are always consistent
5. **⚡ Performance**: Async architecture handles high throughput with low latency
6. **🧪 Quality**: 80% test coverage requirement catches bugs before production

### When to Use Hexagonal Architecture ✅

**Ideal for:**
- **Payment systems** where provider flexibility is critical (easily add Adyen, Square, etc.)
- **Long-lived applications** that will evolve over 5+ years
- **Multi-tenant systems** where different clients need different integrations
- **Regulated domains** (finance, healthcare) requiring strict business rules separation
- **Microservices** with complex domain logic independent of infrastructure
- **Team scaling** where domain experts and infrastructure engineers work in parallel
- **Testing-critical systems** requiring extensive mocking and isolation

**Example scenarios:**
- Marketplace platforms supporting multiple payment gateways per merchant
- B2B SaaS needing custom integrations per enterprise customer
- Financial applications with complex refund/chargeback workflows
- Systems migrating between cloud providers or databases

### When NOT to Use Hexagonal Architecture ❌

**Avoid for:**
- **Simple CRUD apps** with minimal business logic (over-engineering)
- **Proof-of-concepts** or MVPs where speed > structure
- **Single-use scripts** or data processing pipelines
- **Tight deadlines** with small teams (learning curve overhead)
- **Read-heavy applications** with simple queries (layered is sufficient)
- **Throwaway prototypes** that won't be maintained

**Example scenarios:**
- Admin dashboard reading from database and displaying tables
- Batch jobs transforming CSV files without complex rules
- Weekend hackathon projects
- Internal tools with 1-2 developers

### Real-World Impact

**Before Hexagonal:**
```python
# Tightly coupled to Stripe
def charge_customer(amount, card_token):
    stripe.Charge.create(amount=amount, source=card_token)
    db.save_payment(...)
```
❌ Changing to PayPal requires rewriting entire payment flow  
❌ Testing requires hitting real Stripe API  
❌ Business rules scattered across infrastructure code

**After Hexagonal:**
```python
# Domain-driven with injected dependencies
class ProcessPayment:
    def __init__(self, payment_repo, provider, events):
        # Ports injected - implementation doesn't matter
        ...
    
    async def execute(self, request):
        # Pure business logic
        payment = Payment(...)  # Domain entity
        payment.mark_processing(...)
        await self.provider.charge(...)  # Abstract port
```
✅ Add PayPal by implementing `PaymentProvider` interface  
✅ Test with mocked ports - no external calls  
✅ Business rules in domain entities - single source of truth

## Architecture Overview

This project demonstrates **Hexagonal Architecture** (also known as Ports and Adapters pattern) with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                      │
│                    [HTTP Routes & Dependencies]                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Application Layer                           │
│  ┌────────────────┐              ┌─────────────────────────┐   │
│  │  Use Cases     │◄─────────────┤  Ports (Interfaces)     │   │
│  │ • ProcessPayment│              │ • PaymentRepository     │   │
│  │ • RefundPayment │              │ • PaymentProvider       │   │
│  │ • GetStatus     │              │ • EventPublisher        │   │
│  └────────────────┘              │ • IdempotencyStore      │   │
│                                   └─────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       Domain Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Entities    │  │Value Objects │  │  Domain Exceptions   │  │
│  │ • Payment    │  │ • Amount     │  │ • InvalidAmount      │  │
│  │ • Transaction│  │ • Status     │  │ • PaymentNotFound    │  │
│  │ • Customer   │  │ • Method     │  │ • RefundExceeds...   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Infrastructure Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Repositories│  │   Providers   │  │   Adapters           │   │
│  │ PostgreSQL  │  │ Stripe        │  │ RabbitMQ Publisher   │   │
│  │ (SQLAlchemy)│  │ PayPal        │  │ Redis Idempotency    │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Dependency Inversion**: Domain layer has zero external dependencies
2. **Interface Segregation**: Ports defined as `typing.Protocol` interfaces
3. **Separation of Concerns**: Each layer has distinct responsibilities
4. **Testability**: Easy to test with mocked adapters
5. **Flexibility**: Simple to swap implementations (e.g., MongoDB instead of PostgreSQL)

## Features

- ✅ **Hexagonal Architecture** with ports & adapters pattern
- ✅ **Transactional Outbox** — reliable event publishing with exactly-once semantics
- ✅ **Background Outbox Worker** — integrated in FastAPI lifespan
- ✅ **Multiple Payment Providers** (Stripe, PayPal, Mock) via adapter pattern
- ✅ **PostgreSQL** for transactional persistence (SQLAlchemy async)
- ✅ **RabbitMQ** for event publishing (payment lifecycle events)
- ✅ **Redis** for idempotency (prevent duplicate charges)
- ✅ **FastAPI** with OpenAPI documentation
- ✅ **Strict Typing** (Python 3.14+ with full type annotations)
- ✅ **Observability** (Loki + Grafana for logs)
- ✅ **Comprehensive Tests** (unit + integration with testcontainers)
- ✅ **CI/CD** (GitHub Actions with 80% coverage requirement)

## Tech Stack

| Component           | Technology                     |
|---------------------|--------------------------------|
| **Framework**       | FastAPI 0.115+                 |
| **Database**        | PostgreSQL 16 + SQLAlchemy 2.0 |
| **Message Queue**   | RabbitMQ 3.13                  |
| **Cache/Idempotency** | Redis 7                       |
| **Payment Providers** | Stripe, PayPal, MockAdapter   |
| **Logging**         | Loki + Grafana + Promtail      |
| **Testing**         | pytest + testcontainers        |

## 🚀 Quick Start

```bash
# Start infrastructure
docker compose up -d

# Install dependencies  
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start server (with integrated outbox worker)
uvicorn arch_hexagonal_postgresql_fast.adapters.api.fastapi_app:app --reload

# Test payment
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust_001","amount":99.99,"currency":"USD","payment_method":"credit_card","payment_method_token":"tok_visa","idempotency_key":"unique_001"}'
```

**Swagger UI:** http://localhost:8000/docs

See [QUICKSTART.md](QUICKSTART.md) for detailed setup.

# Start infrastructure
docker compose up -d

# Run application
python -m arch_hexagonal_postgresql_fast.main
```

## 🚀 API Usage

### Process Payment

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_123",
    "amount": 100.50,
    "currency": "USD",
    "payment_method": "credit_card",
    "payment_method_token": "tok_visa_4242",
    "idempotency_key": "unique_key_123",
    "provider": "stripe"
  }'
```

### Refund Payment

```bash
curl -X POST "http://localhost:8000/api/v1/payments/{payment_id}/refund" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.00,
    "idempotency_key": "refund_key_456"
  }'
```

### Get Payment Status

```bash
curl "http://localhost:8000/api/v1/payments/{payment_id}"
```

## 🛠️ Development

```bash
ruff check .      # Linting
ruff format .     # Formatting
mypy src          # Type checking
pytest            # Tests with coverage
```

## 📋 Standards

- ✅ Strict typing (mypy strict)
- ✅ 80%+ test coverage
- ✅ Auto-formatting (ruff)
- ✅ Secret detection
- ✅ Hexagonal architecture pattern
- ✅ Domain-driven design principles

## Why RabbitMQ over Kafka?

For a payment service, **RabbitMQ** was chosen because:

1. **Simpler Setup**: Single Docker container vs Kafka cluster
2. **Task Queue Pattern**: Perfect for payment confirmation tasks
3. **Native Transactions**: Aligns with PostgreSQL ACID semantics
4. **Lower Latency**: Better for synchronous payment flows
5. **Sufficient Throughput**: Payment services rarely need 100k+ msg/s

## License

MIT
