
# IROP Re-accommodation Dashboard

This package now contains both the original IOC views and a new Realtime Flight Monitor for Cathay Pacific’s Hong Kong departures. The monitor is backed by a FastAPI service that synthesizes live-style data for CX flights (alerts, turn progress, connection risk, etc.).

## Prerequisites
- Node.js 18+
- Python 3.10+ (for the backend service)

## Frontend (Vite + React)
1. `cd frontend/dashboard`
2. Copy `.env.example` to `.env.local` (or `.env`) and adjust:
   - `VITE_MONITOR_API` if your backend is not running on `http://localhost:8000`.
   - `VITE_DEFAULT_MONITOR_MODE` (`synthetic` or `realtime`) if you want the UI to boot into a specific data source.
   - `VITE_AGENTIC_APIV2_BASE` when you want the UI toggle to hit the google_a2a_agents_apiV2 service instead of the local LangGraph backend.
   - `VITE_AGENTIC_DEFAULT_ENGINE` to preselect `langgraph` (default) or `apiv2` in the runtime toggle.
3. Install deps with `npm install`
4. Start the dev server with `npm run dev`

`npm run build` produces the production bundle in `frontend/dashboard/build`. While running `npm run dev` you can flip between realtime and synthetic datasets via the “Select source” dropdown; the hook automatically adds `mode=realtime|synthetic` to each API poll.

The Realtime Monitor, IOC dashboard, and Agentic Debug Panel now expose an **Agent Runtime** selector (LangGraph v1 vs APIV2 / Google A2A). Set `VITE_AGENTIC_APIV2_BASE` to the Vertex/Cloud Run endpoint if you want the toggle to call the Gemini+Amadeus stack; leave it blank to keep using the built-in LangGraph workflow.
## Backend (FastAPI)
1. `cd backend`
2. Create a virtual env: `python -m venv .venv && source .venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Run locally: `uvicorn app.main:app --reload --port 8000`
5. (Optional) Copy `backend/.env.example` to `.env` and configure:
   - `FLIGHT_MONITOR_MODE` to set the default provider (`synthetic` for deterministic demo data, `realtime` for aviationstack pulls).
   - `AVIATIONSTACK_API_KEY` (required for realtime mode) and `AVIATIONSTACK_BASE_URL` if you proxy the service.

The React app polls `GET /api/flight-monitor` every 30 seconds, passes the selected `mode`, and exposes a manual refresh button inside the Realtime Monitor tab.
  
