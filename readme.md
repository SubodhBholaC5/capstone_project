# Price Pack Architecture Copilot

Runnable POC boilerplate: **Streamlit → FastAPI → Python simulator**, with optional OpenAI Responses API function calling.
Compare what happens to volume, revenue, gross profit and margin when prices change while a pack stays fixed.
All included calibration is synthetic. No source notebook or business dataset was supplied.

## Quick start

Run these commands from this repository directory (`capstone_project`), with [uv](https://docs.astral.sh/uv/) installed:

```powershell
uv sync --frozen
Copy-Item .env.example .env
uv run python -m price_pack_copilot.main
```

In another terminal in the same directory:

```powershell
uv run streamlit run src/price_pack_copilot/frontend.py
```

Open Streamlit at `http://localhost:8501`. The API defaults to `http://127.0.0.1:8000` and its interactive docs to `/docs`.
Choose a fixed pack and compare `9, 10, 11, 15` for the 330 ml six-pack: the last price is explicitly refused.
The UI preserves losing scenarios, shows baselines, and displays assumptions alongside results.

## Configuration

`.env` is local and ignored by Git; `.env.example` is the tracked template. Existing environment variables take priority.
The local `.env` initially contains no secrets. Paths are relative to your working directory.

| Variable | Purpose |
| --- | --- |
| `PPA_CATALOG_PATH` | Validated JSON calibration file |
| `PPA_API_URL` | Backend URL used by Streamlit |
| `PPA_REQUEST_TIMEOUT_SECONDS` | Manual UI HTTP timeout |
| `PPA_SIMULATION_BUDGET_MS` | Measured simulator time target, excluding HTTP/AI |
| `PPA_LOG_LEVEL` | Application logging level |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Optional provider credentials and model ID supporting Responses function calling |
| `OPENAI_RESPONSES_URL` | HTTPS Responses endpoint |
| `PPA_LLM_TIMEOUT_SECONDS` | Timeout per provider request; two requests per question |
| `PPA_MAX_OUTPUT_TOKENS` | Output limit per provider request |

For natural-language mode, set the API key and an accessible model ID on the backend, restart it, and ask:
`Compare demo_330ml_6pk at prices 9 and 11`. Manual comparison works without these settings.
Natural-language questions and synthetic calibration are sent to the configured provider; calls use `store=false`.
Model explanations are labeled separately; Python output is the numerical source of truth.

## Project structure

```text
capstone_project/
├── .env                         # local, ignored
├── .env.example
├── .gitignore
├── .python-version
├── .github/workflows/ci.yml
├── pyproject.toml
├── uv.lock
├── readme.md
├── configs/catalog.json
├── docs/
│   ├── architecture.md
│   └── what_changed.md
├── notebook/readme.md
├── data/
│   ├── readme.md
│   ├── raw/.gitkeep
│   └── processed/.gitkeep
├── src/price_pack_copilot/
│   ├── __init__.py
│   ├── api.py
│   ├── config.py
│   ├── frontend.py
│   ├── main.py
│   ├── models.py
│   └── services/
│       ├── __init__.py
│       ├── catalog.py
│       ├── copilot.py
│       └── simulator.py
└── tests/
    ├── fixtures/malformed_catalog.json
    ├── conftest.py
    ├── test_api.py
    ├── test_catalog.py
    ├── test_config.py
    ├── test_copilot.py
    ├── test_frontend.py
    ├── test_main.py
    ├── test_models.py
    ├── test_package.py
    └── test_simulator.py
```

## Validation

```powershell
uv run black --check src tests
uv run isort --check-only src tests
uv run mypy
uv run pytest
```

GitHub Actions runs all four on every pull request and pushes to `main`. Enable the `validate` check
as required in GitHub branch protection to enforce merge blocking; workflow configuration alone cannot do that.
Tests use in-process API requests and a mocked provider; no key, external API call or running server is required.

See [architecture](docs/architecture.md) for contracts, formula, metric definitions and POC boundaries,
and [what changed](docs/what_changed.md) for the requirement-to-module mapping.
