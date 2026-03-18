# Repository Guidelines

## Project Structure & Module Organization
Core application code lives in `app/`. Use `app/main.py` for the FastAPI entry point, `app/routers/` for HTTP routes, `app/services/` for business logic and integrations, `app/models/` for Pydantic models, `app/middleware/` for request/error handling, and `app/utils/` for shared helpers. Tests live in `tests/` with active coverage centered on `tests/unit/`; integration tests sit in `tests/integration/`, and `tests/e2e/` is reserved for broader workflow checks. Deployment and operational files are at the repo root: `Dockerfile`, `cloudbuild.yaml`, `setup-cloudbuild.sh`, and `.env.example`.

## Build, Test, and Development Commands
Install dependencies with `uv sync`. Run the service locally with `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080`. Use `uv run pytest` for the default test suite and `./run_tests.sh all` to run the repo’s scripted test flow. Target a subset with `./run_tests.sh unit`, `./run_tests.sh integration`, or `uv run pytest tests/unit/test_health.py`. Check style with `uv run ruff check .`, format with `uv run ruff format .`, and type-check with `uv run mypy app`.

## Coding Style & Naming Conventions
This codebase targets Python 3.11, uses 4-space indentation, double quotes, and a 100-character line length. Keep imports sorted and grouped by Ruff/isort. Follow existing naming patterns: `snake_case` for modules, functions, and variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants and environment keys. Prefer explicit typing because `mypy` runs in strict mode.

## Testing Guidelines
Pytest is the test runner, with coverage enforced at `--cov-fail-under=80` for `app/`. Name files `test_*.py` or `*_test.py`, and use markers such as `@pytest.mark.unit` or `@pytest.mark.integration` when categorizing tests. Add unit tests for new service, router, and validation paths; mock Google Cloud, SMTP, and external AI clients rather than hitting live services.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commits, often with prefixes like `feat:` and `fix:`. Keep that style: `feat: add firestore tracker`, `fix: handle invalid pubsub payload`. Pull requests should include a concise summary, linked issue or task when relevant, the commands you ran (`uv run pytest`, `uv run ruff check .`), and sample request/response payloads or screenshots when behavior changes affect API consumers or operations.

## Security & Configuration Tips
Never commit `.env.local`, service-account keys, or SMTP credentials. Start from `.env.example`, prefer `gcloud auth application-default login` for local work, and keep production secrets in Google Secret Manager / Cloud Run configuration rather than source control.
