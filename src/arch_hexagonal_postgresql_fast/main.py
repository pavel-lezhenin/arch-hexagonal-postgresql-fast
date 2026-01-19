"""Main entry point."""

from __future__ import annotations

import uvicorn


def main() -> None:
    """Run the application."""
    uvicorn.run(
        "arch_hexagonal_postgresql_fast.adapters.api.fastapi_app:app",
        host="0.0.0.0",  # nosec B104 - Required for Docker/container environments
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
