from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .exceptions import ProviderConfigError, ProviderDataError
from .providers import ProviderMode, resolve_provider
from .routes import agentic, agent_reaccommodation, agent_options, reaccommodation
from .services import reaccommodation as reaccom_service
from .services import mongo_client

app = FastAPI(
    title="Cathay Realtime/Data Flight Monitor",
    description="Backend service that powers the HKG-focused realtime dashboard with LangGraph agentic analysis",
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

    try:
        return await _load_payload(selected_mode, airport, carrier)
    except ProviderConfigError as exc:
        if selected_mode != "realtime":
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        payload = await _load_payload("synthetic", airport, carrier)
        payload["fallbackReason"] = str(exc)
        return payload
    except ProviderDataError as exc:
        if selected_mode != "realtime":
            status = 500
            raise HTTPException(status_code=status, detail=str(exc)) from exc
        payload = await _load_payload("synthetic", airport, carrier)
        payload["fallbackReason"] = str(exc)
        return payload


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Ensure Mongo clients are closed on shutdown."""
    mongo_client.close_client()
