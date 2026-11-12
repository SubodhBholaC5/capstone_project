"""Backend command-line entry point."""

import logging

import uvicorn

from price_pack_copilot.config import load_settings


def main() -> None:
    """Start the local API with validated logging configuration."""
    settings = load_settings()
    logging.basicConfig(level=settings["log_level"], format="%(asctime)s %(levelname)s %(name)s %(message)s")
    uvicorn.run("price_pack_copilot.api:create_app", factory=True)


if __name__ == "__main__":
    main()
