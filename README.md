# arch-hexagonal-postgresql-fast

Hexagonal architecture with PostgreSQL and payment processing

## 📦 Installation

```bash
# From GitHub
pip install git+https://github.com/yourname/arch-hexagonal-postgresql-fast.git

# For development
git clone https://github.com/yourname/arch-hexagonal-postgresql-fast.git
cd arch-hexagonal-postgresql-fast
pip install -e ".[dev]"
pre-commit install
```

## 🚀 Usage

```python
from arch_hexagonal_postgresql_fast import Client

async with Client() as client:
    result = await client.request()
```

## 🛠️ Development

```bash
ruff check .      # Linting
ruff format .     # Formatting
mypy src          # Type checking
pytest            # Tests
```

## 📋 Standards

- ✅ Strict typing (mypy strict)
- ✅ 80%+ test coverage
- ✅ Auto-formatting (ruff)
- ✅ Secret detection
