import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .exceptions import ProviderConfigError, ProviderDataError
from .providers import ProviderMode, resolve_provider
from .routes import agentic, agent_reaccommodation, agent_options, reaccommodation, whatif
from .services import reaccommodation as reaccom_service
from .services import mongo_client
from .services.predictive_signals import compute_predictive_signals
from .services.disruption_updater import get_disruption_updater
from .agentsv2 import api as agentsv2_api

# Configure logging to show INFO level and above
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(name)s - %(message)s',
)

# Set specific loggers to INFO to see agent communications
logging.getLogger("app.routes.agent_options").setLevel(logging.INFO)
logging.getLogger("app.services.agentic").setLevel(logging.INFO)
logging.getLogger("app.agentsv2.workflow").setLevel(logging.INFO)
logging.getLogger("app.agentsv2.agents").setLevel(logging.INFO)

app = FastAPI(
    title="Cathay Realtime/Data Flight Monitor",
    description="Backend service that powers the HKG-focused realtime dashboard with APIV2 (ADK) agentic analysis",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reaccommodation.router)
app.include_router(agent_reaccommodation.router)
app.include_router(agent_options.router)
app.include_router(agentic.router)
app.include_router(agentsv2_api.router)
app.include_router(whatif.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok", "defaultMode": settings.default_mode}


async def _load_payload(
    target_mode: ProviderMode, airport: str, carrier: str
) -> dict:
    provider = resolve_provider(target_mode)
    return await provider.get_payload(airport.upper(), carrier.upper())


@app.get("/api/flight-monitor", tags=["flight-monitor"])
async def get_flight_monitor(
    airport: str = Query("HKG", description="IATA code of the station"),
    carrier: str = Query("CX", description="Airline designator"),
    mode: Literal["synthetic", "realtime", "mongo"] | None = Query(
        None, description="Data source to use (defaults to FLIGHT_MONITOR_MODE)"
    ),
) -> dict:
    """Return live flight stats plus crew + aircraft readiness panels."""
    selected_mode: ProviderMode = (mode or settings.default_mode)  # type: ignore[assignment]

    payload: dict
    try:
        payload = await _load_payload(selected_mode, airport, carrier)
    except ProviderConfigError as exc:
        if selected_mode != "realtime":
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        payload = await _load_payload("synthetic", airport, carrier)
        payload["fallbackReason"] = str(exc)
    except ProviderDataError as exc:
        if selected_mode != "realtime":
            status = 500
            raise HTTPException(status_code=status, detail=str(exc)) from exc
        payload = await _load_payload("synthetic", airport, carrier)
        payload["fallbackReason"] = str(exc)

    # Attach predictive signals so the UI can show AI guidance without a full run
    try:
        payload["predictiveSignals"] = compute_predictive_signals(payload)
    except Exception:
        payload["predictiveSignals"] = None

    return payload


@app.get("/api/predictive-alerts/{flight_number}", tags=["flight-monitor"])
async def get_predictive_alerts(
    flight_number: str,
    airport: str = Query("HKG", description="IATA code of the station"),
    carrier: str = Query("CX", description="Airline designator"),
    mode: Literal["synthetic", "realtime", "mongo"] | None = Query(
        None, description="Data source to use (defaults to FLIGHT_MONITOR_MODE)"
    ),
) -> dict:
    """
    Fetch predictive signal alerts for a specific flight.
    
    Returns detailed predictive insights including risk drivers, probability,
    and recommended actions for the specified flight.
    """
    selected_mode: ProviderMode = (mode or settings.default_mode)  # type: ignore[assignment]

    # Get the full payload to find the flight
    try:
        payload = await _load_payload(selected_mode, airport, carrier)
    except (ProviderConfigError, ProviderDataError) as exc:
        if selected_mode == "realtime":
            payload = await _load_payload("synthetic", airport, carrier)
        else:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Find the specific flight
    flights = payload.get("flights", [])
    flight = next(
        (f for f in flights if f.get("flightNumber") == flight_number.upper()),
        None,
    )

    if not flight:
        raise HTTPException(
            status_code=404,
            detail=f"Flight {flight_number} not found in {airport}/{carrier}",
        )

    # Get predictive alert if it exists
    predictive_alert = flight.get("predictiveAlert")
    
    if not predictive_alert:
        # Generate generic alert if none exists
        updater = get_disruption_updater()
        signals = updater.get_latest_signals()
        
        return {
            "flightNumber": flight_number,
            "hasPredictiveAlert": False,
            "message": "No specific predictive alerts for this flight",
            "generalSignals": signals,
        }

    return {
        "flightNumber": flight_number,
        "hasPredictiveAlert": True,
        "alert": predictive_alert,
        "flightStatus": {
            "statusCategory": flight.get("statusCategory"),
            "status": flight.get("status"),
            "delayMinutes": flight.get("delayMinutes", 0),
            "paxImpacted": flight.get("paxImpacted", 0),
        },
    }


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Ensure Mongo clients are closed on shutdown."""
    mongo_client.close_client()
