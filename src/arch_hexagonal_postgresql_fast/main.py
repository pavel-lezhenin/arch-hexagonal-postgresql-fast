"""Main entry point."""

from __future__ import annotations

import uvicorn

from arch_hexagonal_postgresql_fast.adapters.api.fastapi_app import app


def main() -> None:
    """Run the application."""
    uvicorn.run(
        "arch_hexagonal_postgresql_fast.adapters.api.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
