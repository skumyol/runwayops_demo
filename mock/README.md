# Cathay Mock Data

This folder stores JSON payloads for crew, passengers, aircraft, and disruption scenarios (including flight-manifest snapshots). Generate fresh datasets any time with `scripts/generate_mock_data.py`:

```bash
uv run --with backend python scripts/generate_mock_data.py --flights 12 --base-passengers 200
```

The script now writes the following files so they can be served statically (for example, `fetch('/mock/passengers.json')`) or ingested by FastAPI/LangGraph workloads:

- `crew.json`
- `passengers.json`
- `disruptions.json`
- `flight_manifests.json`
- `flight_records.json` (new crew/aircraft/pax join layer)
- `aircraft.json` (Cathay fleet with maintenance metadata)

MongoDB collections mirror the same payloads, so you can point the backend at the generated dataset without additional imports. Use the new `--no-json`, `--no-mongo`, and `--no-kafka` flags if you need to target a specific sink only.

### Crew + aircraft quick panels

- `crew.json` rows now include `fatigueRisk`, `currentDutyPhase`, `readinessState`, `statusNote`, and `commsPreference`. These drive the dashboard’s crew tab without another lookup.
- `aircraft.json` adds a `statusNotes` string so the UI can surface a concise readiness summary alongside the flight-specific gate/turn data.
- When you regenerate fixtures, FastAPI will automatically expose these panels via `/api/flight-monitor` for both the Mongo and synthetic providers.

### Realtime ticker + Mongo provider

1. Seed MongoDB (requires `mongod` running locally):

   ```bash
   backend/.venv/bin/python scripts/generate_mock_data.py --flights 12 --base-passengers 200
   ```

2. Keep the data stream fresh with:

   ```bash
   backend/.venv/bin/python scripts/flight_ticker.py --sleep 30
   ```

   The ticker nudges `flight_instances` every 30 seconds so the new `mongo` provider can power the dashboard without going through aviationstack.

3. Point FastAPI at Mongo by setting `FLIGHT_MONITOR_MODE=mongo` (see `backend/.env` for an example) and restart `uvicorn`.
