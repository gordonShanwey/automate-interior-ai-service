# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run application locally
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Run all unit tests (default pytest config points to tests/unit/)
uv run pytest

# Run tests without coverage (faster)
uv run pytest --no-cov

# Run specific test file
uv run pytest tests/unit/test_health.py

# Run specific test function
uv run pytest tests/unit/test_health.py::TestHealthEndpoints::test_health_check_basic

# Run integration tests (not in default testpath)
uv run pytest tests/integration/

# Run by marker
uv run pytest -m unit
uv run pytest -m "not slow"

# Lint and format
uv run ruff check .
uv run ruff format .
uv run ruff check --fix .

# Type check
uv run mypy app
```

## Architecture

This is a **FastAPI service** that automates interior designer workflows. The core data flow is:

1. **Pub/Sub push → `/webhooks/pubsub`** — Google Pub/Sub delivers client form submissions as base64-encoded JSON payloads to this endpoint
2. **Background task** — The webhook immediately returns 204 and offloads processing via `BackgroundTasks`
3. **PubSubService** (`app/services/pubsub_service.py`) — Validates and normalizes raw form data into `RawClientData`
4. **ClientFormData** (`app/models/client_data.py`) — Converts `RawClientData` into structured fields; handles two input shapes: array-indexed (Polish Google Form format with `values[]`) and key-value dict (fallback)
5. **GenAIService** (`app/services/genai_service.py`) — Calls Vertex AI (gemini-2.5-pro) with a structured prompt; expects JSON back with design recommendations
6. **EmailService** (`app/services/email_service.py`) — Sends the generated `ClientProfile` report to the designer via SMTP

**Retry handling**: The `/webhooks/pubsub` endpoint tracks per-message retry counts in memory. After `MAX_ENDPOINT_RETRIES=3` failures it always returns 204 (acknowledge) to prevent infinite Pub/Sub redelivery loops.

**Services are singletons** initialized lazily via module-level `get_*_service()` functions.

**Config** (`app/config.py`) uses `pydantic-settings` with `.env.local` as the env file. Required fields: `GOOGLE_CLOUD_PROJECT`, `DESIGNER_EMAIL`. Optional at startup but needed for actual processing: `SMTP_USERNAME`, `SMTP_PASSWORD`.

**Docs/OpenAPI** are only exposed when `DEBUG=true` (at `/docs`, `/redoc`).

## Key Notes

- `pytest.ini_options.testpaths = ["tests/unit"]` — default `uv run pytest` only runs unit tests; use explicit path for integration/e2e
- Coverage threshold is 80%; CI will fail below this
- `ClientFormData.from_raw_data()` contains hardcoded array index mappings for a specific Polish Google Form (`values[3]` = name, `values[1]` = email, etc.) — this is intentional for the real client's form structure
- Services use module-level globals for singleton instances; in tests, these need to be patched
- All Google Cloud services (GenAI, Pub/Sub) require either `GOOGLE_APPLICATION_CREDENTIALS` or `gcloud auth application-default login`
