# Repository Guidelines

## Project Structure & Module Organization
Backend FastAPI lives in `backend/` with `app/main.py` as the uvicorn entrypoint and provider logic split across `app/providers/{synthetic,realtime,shared}.py` plus typed settings in `app/config.py`. The Vite + React dashboard sits in `frontend/dashboard`, where `src/views` hold page flows, `src/components/ui` wraps shadcn primitives, and `src/hooks` orchestrate polling. Mock fixtures are tracked under `mock/` and refreshed via `scripts/generate_mock_data.py`; use `run_dev.sh` whenever you need backend (8000) and UI (3000) in lockstep.

## Build, Test, and Development Commands
- `./run_dev.sh` — resets ports, warms `.uv-cache`, and launches FastAPI + Vite with shared logs.
- `cd backend && uv run uvicorn app.main:app --reload --port 8000` — backend only; install with `uv pip install -r requirements.txt`.
- `cd frontend/dashboard && npm install` — install UI deps (pnpm works because `pnpm-lock.yaml` is present).
- `cd frontend/dashboard && npm run dev` — Vite dev server honoring `.env` and `VITE_MONITOR_API`.
- `cd frontend/dashboard && npm run build` — outputs the static bundle into `frontend/dashboard/build/`.
- `python scripts/generate_mock_data.py` — refreshes crew/passenger/disruption fixtures referenced by the dashboard.

## Coding Style & Naming Conventions
Python targets 3.12; keep 4-space indents, exhaustive type hints, and module-level docstrings that explain fallbacks (see `app/main.py`). Provider classes should expose `get_payload` and return serializable dicts; name functions with `snake_case` and constants in `UPPER_SNAKE`. React code is TypeScript-first with `PascalCase` components, `useCamelCase` hooks, and barrelled exports in `src/components/ui`. Prefer Tailwind utility classes from `src/index.css`, reserve custom selectors for shared tokens.

## Testing Guidelines
Automated tests are not yet wired up, so add them alongside new features. Backend suites should live in `backend/tests`, rely on `pytest` + `pytest-asyncio`, and hit `app` through `httpx.AsyncClient`. Frontend coverage should use `vitest` with `@testing-library/react`; name files `<Component>.test.tsx` and stage fixtures under `src/__tests__/fixtures`.

## Commit & Pull Request Guidelines
Because this snapshot ships without `.git`, align on Conventional Commit syntax once cloned (e.g., `feat: add realtime fallback banner`). Keep bodies wrapped at ~72 characters and mention affected dirs (`backend`, `frontend/dashboard`, `mock`). Pull requests must describe behavior, link the Runway issue, list manual verification (commands run, screenshots for UI), and call out any regenerated JSON payloads.

## Security & Configuration Tips
Store secrets in `.env` files (`backend/.env`, `frontend/dashboard/.env.local`) and never commit `AVIATIONSTACK_API_KEY`. Default to `FLIGHT_MONITOR_MODE=synthetic` locally so the UI can boot without the aviationstack quota. Ports 8000/3000 are hard-coded in `run_dev.sh`; adjust there instead of editing multiple scripts.
