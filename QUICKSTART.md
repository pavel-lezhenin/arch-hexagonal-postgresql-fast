# Quick Start Guide

Get the payment service running locally in 5 minutes.

## Prerequisites

- Python 3.14+
- Docker & Docker Compose
- Git

## Step 1: Clone and Navigate

```bash
cd packages/arch-hexagonal-postgresql-fast
```

## Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install package with dev dependencies
pip install -e ".[dev]"
```

## Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env` file with your credentials:

```env
# Stripe (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_API_KEY=sk_test_your_actual_stripe_test_key
STRIPE_ENABLED=true

# PayPal (optional, get from https://developer.paypal.com/)
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=sandbox
PAYPAL_ENABLED=false
```

## Step 4: Start Infrastructure

```bash
# Start PostgreSQL, RabbitMQ, Redis, and observability stack
docker compose up -d

# Verify services are running
docker compose ps

# Expected output:
# payment_postgres    Up    0.0.0.0:5432->5432/tcp
# payment_rabbitmq    Up    0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
# payment_redis       Up    0.0.0.0:6379->6379/tcp
# payment_grafana     Up    0.0.0.0:3000->3000/tcp
```

## Step 5: Run Application

```bash
# Start FastAPI server
python -m arch_hexagonal_postgresql_fast.main

# Or use uvicorn directly
uvicorn arch_hexagonal_postgresql_fast.adapters.api.fastapi_app:app --reload
```

Application starts at: **http://localhost:8000**

## Step 6: Explore API

### OpenAPI Documentation
Visit **http://localhost:8000/docs** for interactive API documentation.

### Example: Process Payment

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_test_123",
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card",
    "payment_method_token": "tok_visa",
    "idempotency_key": "unique_12345",
    "provider": "stripe"
  }'
```

### Example: Get Payment Status

```bash
curl "http://localhost:8000/api/v1/payments/{payment_id}"
```

### Example: Refund Payment

```bash
curl -X POST "http://localhost:8000/api/v1/payments/{payment_id}/refund" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.00,
    "idempotency_key": "refund_67890"
  }'
```

## Step 7: Run Tests

```bash
# All tests with coverage
pytest --cov=src --cov-report=html

# Unit tests only (fast)
pytest tests/unit -v

# Integration tests (requires Docker)
pytest tests/integration -v

# View coverage report
open htmlcov/index.html   # Mac
start htmlcov/index.html  # Windows
```

## Monitoring & Observability

### RabbitMQ Management UI
- URL: http://localhost:15672
- Username: `guest`
- Password: `guest`

### Grafana Dashboards
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`

### View Logs
1. Open Grafana (http://localhost:3000)
2. Go to "Explore"
3. Select "Loki" datasource
4. Query: `{job="payment_service"}`

## Development Workflow

### 1. Make Changes
Edit code in `src/arch_hexagonal_postgresql_fast/`

### 2. Run Linting
```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### 3. Type Checking
```bash
mypy src/
```

### 4. Run Tests
```bash
pytest -v
```

### 5. Pre-commit Checks
```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Troubleshooting

### Database Connection Error
```bash
# Ensure PostgreSQL is running
docker compose ps postgresql

# Check logs
docker compose logs postgresql
```

### RabbitMQ Connection Error
```bash
# Restart RabbitMQ
docker compose restart rabbitmq

# Wait for healthcheck
docker compose ps rabbitmq
```

### Stripe API Key Invalid
- Get test key from https://dashboard.stripe.com/test/apikeys
- Must start with `sk_test_`
- Update `.env` file

### Port Already in Use
```bash
# Change ports in docker-compose.yml
# Example: PostgreSQL 5432 -> 5433
ports:
  - "5433:5432"

# Update DATABASE_URL in .env accordingly
```

## Clean Up

```bash
# Stop all services
docker compose down

# Remove volumes (data will be lost)
docker compose down -v

# Deactivate virtual environment
deactivate
```

## Next Steps

- Read [README.md](README.md) for architecture details
- Explore hexagonal architecture pattern in code
- Add custom payment providers in `adapters/payment_providers/`
- Implement webhook handlers for Stripe/PayPal callbacks
- Add more use cases in `application/use_cases/`

## Support

For issues or questions:
- Check parent repository documentation
- Review CI/CD logs in `.github/workflows/ci.yml`
- Inspect Docker logs: `docker compose logs -f`

## Testing with Real Stripe

### Get Test Card Numbers
Stripe provides test cards: https://stripe.com/docs/testing

```python
# Success
card_number = "4242424242424242"

# Decline (insufficient funds)
card_number = "4000000000009995"

# Require authentication
card_number = "4000002500003155"
```

### Create Payment Method Token
Use Stripe.js or API to create token, then pass to API:

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -d '{
    "payment_method_token": "tok_created_via_stripe_api",
    ...
  }'
```

Happy coding! 🚀
