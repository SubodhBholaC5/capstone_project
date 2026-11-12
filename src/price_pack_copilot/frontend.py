"""Streamlit comparison-first interface; all computations are served by FastAPI."""

from typing import Any

import httpx
import streamlit as st

from price_pack_copilot.config import load_settings
from price_pack_copilot.models import Catalog, Comparison, CopilotResponse


def display_comparison(comparison: Comparison) -> None:
    """Display every outcome, measured latency, and the full assumptions."""
    st.caption(f"{comparison.dataset_id} · {comparison.currency} · {comparison.period}")
    st.subheader("Baseline and all candidates")
    rows = [outcome.model_dump() for outcome in comparison.baselines + comparison.scenarios]
    st.dataframe(rows, hide_index=True)
    st.caption(f"Simulator compute time: {comparison.elapsed_ms:.2f} ms (excludes network and AI time)")
    if comparison.budget_exceeded:
        st.warning("Simulation exceeded its configured performance budget.")
    with st.expander("Assumptions and calibration", expanded=True):
        for assumption in comparison.assumptions:
            st.write(assumption)


def main() -> None:
    """Render the planner workflow and handle recoverable serving failures."""
    settings = load_settings()
    st.set_page_config(page_title="Price Pack Architecture Copilot", layout="wide")
    st.title("Price Pack Architecture Copilot")
    st.caption("Synthetic demo · Compare price changes while holding the selected pack constant")
    try:
        with httpx.Client(base_url=settings["api_url"], timeout=settings["request_timeout"]) as client:
            response = client.get("/catalog")
            response.raise_for_status()
            catalog = Catalog.model_validate(response.json())
    except (httpx.HTTPError, ValueError):
        st.error(
            "Cannot load calibration. Start the FastAPI server and check PPA_API_URL and the catalog configuration."
        )
        return
    products = {product.product_id: product for product in catalog.products}
    manual, copilot = st.tabs(["Compare prices", "Ask the copilot"])
    with manual:
        with st.form("comparison_form"):
            product_id = st.selectbox("Fixed pack", list(products), format_func=lambda value: products[value].name)
            prices = st.text_input("Candidate prices, separated by commas", placeholder="9, 10, 11")
            submitted = st.form_submit_button("Compare all candidates")
        product = products[product_id]
        st.caption(
            f"Baseline: {product.baseline_price:g} {catalog.currency} · Supported price interval: "
            f"{product.baseline_price * product.min_price_ratio:g}–"
            f"{product.baseline_price * product.max_price_ratio:g}. Other prices will be refused."
        )
        if submitted:
            try:
                scenarios = [
                    {"label": f"Candidate {index}", "product_id": product_id, "price": float(price.strip())}
                    for index, price in enumerate(prices.split(","), start=1)
                ]
                result = _post(
                    "/scenarios/compare", {"scenarios": scenarios}, settings["request_timeout"], settings["api_url"]
                )
                st.session_state["comparison"] = Comparison.model_validate(result)
            except (ValueError, httpx.HTTPError) as error:
                st.session_state.pop("comparison", None)
                st.error(_error_message(error))
        if "comparison" in st.session_state:
            display_comparison(st.session_state["comparison"])
    with copilot:
        st.caption("Optional: requires server-side OPENAI_API_KEY and OPENAI_MODEL. Questions are sent to OpenAI.")
        question = st.text_area("Planner question", placeholder=f"Compare {product_id} at prices 9 and 11")
        if st.button("Ask and compare", disabled=not question.strip()):
            try:
                timeout = 2 * settings["llm_timeout"] + settings["request_timeout"]
                result = _post("/copilot", {"question": question}, timeout, settings["api_url"])
                st.session_state["answer"] = CopilotResponse.model_validate(result)
            except (httpx.HTTPError, ValueError) as error:
                st.session_state.pop("answer", None)
                st.error(_error_message(error))
        if "answer" in st.session_state:
            answer = st.session_state["answer"]
            display_comparison(answer.comparison)
            st.subheader("AI explanation")
            st.caption("Generated explanation; use the simulator table above as the numerical source of truth.")
            st.write(answer.explanation)


def _post(path: str, payload: dict[str, Any], timeout: float, api_url: str) -> dict[str, Any]:
    with httpx.Client(base_url=api_url, timeout=timeout) as client:
        response = client.post(path, json=payload)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


def _error_message(error: ValueError | httpx.HTTPError) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        return f"Request refused ({error.response.status_code}): {error.response.text}"
    if isinstance(error, httpx.HTTPError):
        return "API request failed. Check that the server is available and retry."
    return "Enter valid positive candidate prices and a supported pack."


if __name__ == "__main__":
    main()
