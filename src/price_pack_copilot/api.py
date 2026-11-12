"""FastAPI application factory and serving boundary."""

import logging

import httpx
from fastapi import FastAPI, HTTPException

from price_pack_copilot.config import load_settings
from price_pack_copilot.models import Catalog, Comparison, ComparisonRequest, CopilotRequest, CopilotResponse
from price_pack_copilot.services.catalog import load_catalog
from price_pack_copilot.services.copilot import answer_question
from price_pack_copilot.services.simulator import compare_scenarios

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the API, failing startup immediately for invalid local configuration.

    Returns:
        API with validated calibration loaded once per worker.

    Raises:
        OSError: If the catalog is unavailable.
        ValueError: If settings or calibration are invalid.
    """
    settings = load_settings()
    catalog = load_catalog(settings["catalog_path"])
    app = FastAPI(title="Price Pack Architecture Copilot", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report readiness after configuration and calibration validation."""
        return {"status": "ok", "dataset_id": catalog.dataset_id}

    @app.get("/catalog", response_model=Catalog)
    def get_catalog() -> Catalog:
        """Expose supported packs and their explicit assumptions."""
        return catalog

    @app.post("/scenarios/compare", response_model=Comparison)
    def compare(request: ComparisonRequest) -> Comparison:
        """Compare candidate prices, retaining losses and explicit refusals."""
        try:
            return compare_scenarios(request, catalog, settings["simulation_budget_ms"])
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/copilot", response_model=CopilotResponse)
    def copilot(request: CopilotRequest) -> CopilotResponse:
        """Interpret a planner question through the optional Responses integration."""
        if not settings["openai_api_key"] or not settings["openai_model"]:
            raise HTTPException(
                status_code=503, detail="Natural-language mode requires server-side OpenAI configuration"
            )
        try:
            return answer_question(request.question, catalog, settings)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except httpx.TimeoutException as error:
            raise HTTPException(status_code=504, detail="Language provider timed out") from error
        except (httpx.HTTPError, RuntimeError, KeyError, TypeError) as error:
            logger.warning("Language provider failed: %s", type(error).__name__)
            raise HTTPException(
                status_code=502, detail="Language provider failed; use the manual comparison"
            ) from error

    return app
