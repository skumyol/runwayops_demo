# Cathay Realtime Flight Monitor Backend

FastAPI service that powers the runway ops dashboard. It can serve either:
- **Synthetic** data (`mode=synthetic`): deterministic, realistic-looking Cathay operational snapshots.
- **Realtime** data (`mode=realtime`): live pulls from [aviationstack](https://aviationstack.com/) filtered to HKG + CX with heuristics to fill IROP context (turn progress, alerts, etc.).

## Prerequisites
- Python 3.10+

## Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Environment
| Variable | Default | Description |
| --- | --- | --- |
| `FLIGHT_MONITOR_MODE` | `synthetic` | Default provider (`synthetic` or `realtime`). |
| `AVIATIONSTACK_API_KEY` | _None_ | Required when `mode=realtime`. |
| `AVIATIONSTACK_BASE_URL` | `https://api.aviationstack.com/v1` | Override only if pointing to a proxy. |

You can leave realtime variables unset in dev; the dashboard will stay on the synthetic generator.

## Running the API
```bash
uvicorn app.main:app --reload --port 8000
```

### Routes
- `GET /health` — liveness probe with the configured default mode.
- `GET /api/flight-monitor?airport=HKG&carrier=CX&mode=realtime` — data payload consumed by the React app. Omit `mode` to use the backend default.

CORS is open by default so the Vite dev server (port 3000) can call the API locally. Adjust `allow_origins` in `app/main.py` before deploying to production.
