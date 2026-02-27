# Repository Guidelines

## Project Structure & Module Organization
This repository is a thin wrapper around the `dcis/` application plus shared workflow docs. Core code lives under `dcis/backend` and `dcis/frontend`. Backend source is in `dcis/backend/src` with tests in `dcis/backend/tests` split by `unit`, `integration`, `e2e`, `performance`, and `security`. Frontend code lives in `dcis/frontend/src`; route files are under `src/app`, reusable UI under `src/components`, state in `src/store`, hooks in `src/hooks`, and browser tests in `dcis/frontend/e2e`. Top-level `rules_and_workflows/` and `.agent/` hold process documentation, not runtime code.

## Build, Test, and Development Commands
Run project commands from `dcis/`.

- `make setup`: install backend dependencies with Poetry, frontend dependencies with `pnpm`, and pre-commit hooks.
- `make test`: run backend `pytest` coverage and frontend Vitest suites.
- `make lint`: run Ruff and mypy for Python, then ESLint for the frontend.
- `make format`: format backend code with Ruff and frontend code with the configured formatter.
- `cd backend && poetry run uvicorn src.main:app --reload`: start the FastAPI API locally.
- `cd frontend && pnpm dev`: start the Next.js app on port 3000.

## Coding Style & Naming Conventions
Python targets 3.11, uses 4-space indentation, type hints, and Ruff-enforced imports and linting. Keep backend modules `snake_case`; examples already in use include `meta_orchestrator.py` and `chat_analytics.py`. TypeScript and TSX use 2-space indentation. Prefer `PascalCase` for React components such as `PlanVisualizer.tsx`, `camelCase` for hooks and utilities, and colocated `*.test.ts(x)` files for unit tests. Let tooling drive formatting: `ruff format`, `ruff check`, `mypy`, and `eslint`.

## Testing Guidelines
Backend tests use `pytest` with `pytest-asyncio`; default settings come from `dcis/backend/pyproject.toml`. Frontend unit tests use Vitest, and end-to-end plus accessibility coverage use Playwright. Name backend tests `test_*.py` and frontend tests `*.test.ts` or `*.spec.ts`. Before opening a PR, run `make test`; for focused checks use `cd frontend && pnpm test:coverage` or `cd frontend && pnpm test:e2e`.

## Commit & Pull Request Guidelines
Recent history shows short subjects with occasional prefixes such as `chore: update dcis submodule ref`. Prefer concise, imperative commits and use a type prefix when it adds clarity, for example `feat: add orchestration metrics endpoint`. PRs should explain scope, note backend/frontend impact, link the related issue, and include screenshots or short recordings for UI changes. Call out new environment variables, schema changes, or Docker/runtime requirements explicitly.
