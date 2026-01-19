# arch-hexagonal-postgresql-fast

Hexagonal architecture (ports & adapters) payment processing service built with FastAPI, PostgreSQL, and multiple payment providers (Stripe, PayPal).

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
- ✅ **Multiple Payment Providers** (Stripe, PayPal) via adapter pattern
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
| **Payment Providers** | Stripe, PayPal                |
| **Logging**         | Loki + Grafana                 |
| **Testing**         | pytest + testcontainers        |

## 📦 Installation

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

Quick start:

```bash
# Clone and navigate
cd packages/arch-hexagonal-postgresql-fast

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env

# Edit .env with your Stripe/PayPal credentials

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
