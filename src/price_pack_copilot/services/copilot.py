"""Responses API interpretation; all numerical outcomes come from Python."""

from typing import Any

import httpx

from price_pack_copilot.config import Settings
from price_pack_copilot.models import Catalog, ComparisonRequest, CopilotResponse
from price_pack_copilot.services.simulator import compare_scenarios


def answer_question(question: str, catalog: Catalog, settings: Settings) -> CopilotResponse:
    """Interpret one question, execute a validated tool, and explain its results.

    Args:
        question: Planner question specifying packs and candidate prices.
        catalog: Trusted calibration; never supplied by the model.
        settings: Server-side provider credentials and request limits.

    Returns:
        Authoritative comparison plus untrusted model-generated explanation.

    Raises:
        RuntimeError: If provider configuration or the provider response is missing.
        ValueError: If tool arguments or requested scenarios are invalid.
        httpx.HTTPError: If the provider request fails.
    """
    if not settings["openai_api_key"] or not settings["openai_model"]:
        raise RuntimeError("Set OPENAI_API_KEY and OPENAI_MODEL to enable natural-language questions")
    tool = {
        "type": "function",
        "name": "compare_scenarios",
        "description": "Compare explicit proposed prices for existing fixed packs using a deterministic simulator.",
        "strict": True,
        "parameters": ComparisonRequest.model_json_schema(),
    }
    instructions = (
        "Interpret price comparison questions using only catalog product IDs. "
        "Never invent pack sizes, prices, or calibration. If prices or packs are ambiguous, ask for clarification. "
        "Use compare_scenarios for numerical outcomes. Never calculate outcomes yourself. "
        "Explain only tool results, including losses, refusals, assumptions, and synthetic-data limitations. "
        "Catalog: " + catalog.model_dump_json()
    )
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    payload: dict[str, Any] = {
        "model": settings["openai_model"],
        "instructions": instructions,
        "tools": [tool],
        "parallel_tool_calls": False,
        "max_output_tokens": settings["max_output_tokens"],
        "store": False,
        "input": messages,
    }
    headers = {"Authorization": f"Bearer {settings['openai_api_key']}"}
    with httpx.Client(timeout=settings["llm_timeout"], headers=headers) as client:
        response = client.post(settings["responses_url"], json=payload)
        response.raise_for_status()
        body = response.json()
        if body.get("status") != "completed":
            raise RuntimeError("Provider did not complete question interpretation")
        calls = [item for item in body["output"] if item["type"] == "function_call"]
        if len(calls) != 1 or calls[0]["name"] != "compare_scenarios":
            raise ValueError("Specify existing packs and explicit candidate prices so a comparison can be made")
        call = calls[0]
        request = ComparisonRequest.model_validate_json(call["arguments"])
        comparison = compare_scenarios(request, catalog, settings["simulation_budget_ms"])
        messages.extend(body["output"])
        messages.append(
            {"type": "function_call_output", "call_id": call["call_id"], "output": comparison.model_dump_json()}
        )
        payload["tool_choice"] = "none"
        response = client.post(settings["responses_url"], json=payload)
        response.raise_for_status()
        body = response.json()
    if body.get("status") != "completed":
        raise RuntimeError("Provider did not complete the explanation")
    explanations: list[str] = []
    for item in body["output"]:
        if item["type"] != "message":
            continue
        explanations.extend(part["text"] for part in item["content"] if part["type"] == "output_text")
    explanation = "\n".join(explanations).strip()
    if not explanation:
        raise RuntimeError("Provider returned no explanation")
    return CopilotResponse(comparison=comparison, explanation=explanation)
