"""Environment configuration without import-time filesystem access."""

import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv


class Settings(TypedDict):
    """Validated runtime configuration schema."""

    catalog_path: Path
    api_url: str
    request_timeout: float
    simulation_budget_ms: float
    log_level: str
    openai_api_key: str
    openai_model: str
    responses_url: str
    llm_timeout: float
    max_output_tokens: int


def load_settings(env_file: str | Path = ".env") -> Settings:
    """Load local environment defaults, preserving process-level overrides.

    Args:
        env_file: Optional dotenv file, resolved against the working directory.

    Returns:
        Validated runtime settings. Relative paths use the working directory.

    Raises:
        ValueError: If a numeric setting or URL is invalid.
    """
    load_dotenv(env_file, override=False)
    settings = Settings(
        catalog_path=Path(os.getenv("PPA_CATALOG_PATH", "configs/catalog.json")),
        api_url=os.getenv("PPA_API_URL", "http://127.0.0.1:8000").rstrip("/"),
        request_timeout=float(os.getenv("PPA_REQUEST_TIMEOUT_SECONDS", "10")),
        simulation_budget_ms=float(os.getenv("PPA_SIMULATION_BUDGET_MS", "200")),
        log_level=os.getenv("PPA_LOG_LEVEL", "INFO").upper(),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", ""),
        responses_url=os.getenv("OPENAI_RESPONSES_URL", "https://api.openai.com/v1/responses"),
        llm_timeout=float(os.getenv("PPA_LLM_TIMEOUT_SECONDS", "30")),
        max_output_tokens=int(os.getenv("PPA_MAX_OUTPUT_TOKENS", "2000")),
    )
    for value in (
        settings["request_timeout"],
        settings["simulation_budget_ms"],
        settings["llm_timeout"],
        settings["max_output_tokens"],
    ):
        if not 0 < value < float("inf"):
            raise ValueError("Timeouts, budgets and token limits must be finite and positive")
    if not settings["api_url"].startswith(("http://", "https://")):
        raise ValueError("PPA_API_URL must be an HTTP(S) URL")
    if not settings["responses_url"].startswith("https://"):
        raise ValueError("OPENAI_RESPONSES_URL must use HTTPS")
    if settings["log_level"] not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("PPA_LOG_LEVEL is invalid")
    return settings
