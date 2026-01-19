# Event-Driven Payment Service - Workers

## Overview

This service implements an event-driven architecture with:
- **Transactional Outbox Pattern** for reliable event publishing
- **Command-based processing** via RabbitMQ
- **Background workers** for async operations
- **Compensation logic** for failure handling

## Architecture

```
API (FastAPI)
    ↓
ProcessPayment Use Case
    ↓
Save to DB + Outbox (Transactional)
    ↓
Outbox Worker → RabbitMQ → Event Consumers
    ↓
Command Worker → Process Commands
```

## Workers

### 1. Outbox Worker

Publishes events from outbox table to RabbitMQ.

**Run:**
```bash
python -m arch_hexagonal_postgresql_fast.cli.run_outbox_worker
```

**Environment:**
- `DATABASE_URL` - PostgreSQL connection string
- `RABBITMQ_URL` - RabbitMQ connection string

**Behavior:**
- Polls outbox table every 5 seconds
- Publishes unpublished events to RabbitMQ
- Marks events as published after successful delivery
- Retries failed events with exponential backoff (max 5 attempts)
- Tracks failed events for DLQ processing

### 2. Command Worker

Consumes commands from RabbitMQ and executes use cases.

**Run:**
```bash
python -m arch_hexagonal_postgresql_fast.cli.run_command_worker
```

**Environment:**
- `DATABASE_URL` - PostgreSQL connection string
- `RABBITMQ_URL` - RabbitMQ connection string
- `REDIS_URL` - Redis connection string (idempotency)
- `STRIPE_API_KEY` - Stripe API key

**Behavior:**
- Consumes from `payment.commands.process` queue
- Executes ProcessPayment use case
- Handles retries via RabbitMQ message requeue
- Uses idempotency keys to prevent duplicates

## Feature Flags

Control rollout via environment variables:

```bash
ENABLE_ASYNC_COMMANDS=true    # Enable command-based processing
ENABLE_OUTBOX_PATTERN=true    # Enable outbox pattern (recommended)
ENABLE_RETRY_LOGIC=true       # Enable retry mechanism
ENABLE_COMPENSATION=true      # Enable compensation for failures
```

## Running with Docker Compose

```yaml
services:
  outbox-worker:
    build: .
    command: python -m arch_hexagonal_postgresql_fast.cli.run_outbox_worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@postgresql:5432/payments_db
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    depends_on:
      - postgresql
      - rabbitmq
    restart: always

  command-worker:
    build: .
    command: python -m arch_hexagonal_postgresql_fast.cli.run_command_worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@postgresql:5432/payments_db
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - REDIS_URL=redis://redis:6379/0
      - STRIPE_API_KEY=${STRIPE_API_KEY}
    depends_on:
      - postgresql
      - rabbitmq
      - redis
    restart: always
```

## Migrations

Run Alembic migrations before starting workers:

```bash
# Initialize database
alembic upgrade head
```

This creates:
- `outbox_events` table for Transactional Outbox Pattern
- Indexes for efficient querying of unpublished events

## Monitoring

- **Outbox Worker**: Logs published event count and DLQ count
- **Command Worker**: Logs processed commands with idempotency keys
- **RabbitMQ Management UI**: http://localhost:15672 (guest/guest)
- **Grafana**: http://localhost:3000 (admin/admin) - for logs via Loki

## Testing

```bash
# Unit tests
pytest tests/unit -v

# Integration tests (requires Docker)
pytest tests/integration -v
```

## Troubleshooting

### Outbox worker not publishing

1. Check database connection
2. Verify RabbitMQ is running: `docker ps | grep rabbitmq`
3. Check logs for errors
4. Query outbox table: `SELECT * FROM outbox_events WHERE published_at IS NULL;`

### Command worker not consuming

1. Verify RabbitMQ queue exists: RabbitMQ Management UI → Queues
2. Check worker logs for connection errors
3. Verify environment variables are set correctly
4. Test RabbitMQ connection: `rabbitmqadmin list queues`

### Events stuck in outbox

- Check `attempts` column: if >= 5, event is in DLQ
- Check `last_error` column for error details
- Manually retry: `UPDATE outbox_events SET attempts = 0 WHERE id = '...'`

## Migration Strategy

The system supports gradual migration from synchronous to event-driven:

1. **Phase 0-1**: Outbox Pattern enabled (events saved transactionally)
2. **Phase 2**: Command infrastructure ready
3. **Phase 3**: Workers running in parallel
4. **Phase 4**: Compensation logic active
5. **Phase 5**: API migration (sync → async with 202 Accepted)

Use feature flags to control rollout per phase.
