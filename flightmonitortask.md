# Flight Monitor Task

## Objective
Create a Cathay Pacific flight monitor focused on Hong Kong (HKG) departures that can swap between realtime data (aviationstack) and synthetic, realistic mock data, while feeding the Vite/React dashboard.

## Backend deliverables
- FastAPI service under `backend/` exposing `GET /api/flight-monitor?airport=HKG&carrier=CX&mode=realtime` and `GET /health`.
- Provider architecture with:
  - `synthetic`: curated Cathay dataset (CX520, CX255, CX865, CX903, CX315, CX685) with alerts, milestones, trends.
  - `realtime`: aviationstack client translating live departures into the same payload (ops readiness, connection risk, irregular ops plan) using heuristics to fill any missing operational context.
- Config via `FLIGHT_MONITOR_MODE`, `AVIATIONSTACK_API_KEY`, `AVIATIONSTACK_BASE_URL`.
- Documentation for prerequisites, env vars, and how to run the API.

## Frontend deliverables
- `RealtimeFlightMonitor` view with:
  - Metric tiles, alert board, trend card, and detailed flight cards.
  - Polling hook (`useFlightMonitor`) that refreshes every 30s, exposes manual refresh + error handling, and respects `VITE_MONITOR_API` + `mode` query string.
  - UI toggle to switch between realtime and synthetic sources, defaulting to the backend’s configured mode.
  - Visual focus on Cathay @ HKG (status chips, progress, milestone timeline, irregular ops playbook hooks) and badges that reveal which source backed the payload.
- `.env.example` and README notes describing how to point dev/prod builds at the right backend mode.
