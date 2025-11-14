"""API routes for LangGraph agentic disruption analysis.

Endpoints:
- POST /api/agentic/analyze: Run agentic analysis on flight data
- GET /api/agentic/history: Retrieve past analyses
- GET /api/agentic/simulations: Retrieve simulation history
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from .._agents.llm_factory import get_provider_info
from ..config import AGENTIC_ENGINES, settings
from ..providers import ProviderMode, resolve_provider
from ..services.agentic import agentic_service
from ..services.scenario_overrides import apply_debug_scenario

router = APIRouter(prefix="/api/agentic", tags=["agentic"])


@router.post("/analyze")
async def analyze_disruption(
    airport: str = Query("HKG", description="IATA code of the station"),
    carrier: str = Query("CX", description="Airline designator"),
    mode: ProviderMode | None = Query(
        None, description="Data source to use (defaults to FLIGHT_MONITOR_MODE)"
    ),
    scenario: str | None = Query(
        None,
        description="Optional debug scenario to apply (delay_3hr, crew_out, weather_groundstop)",
    ),
    engine: str | None = Query(
        None,
        description=f"Agentic engine to run ({', '.join(sorted(AGENTIC_ENGINES))})",
    ),
) -> Dict[str, Any]:
    """Run LangGraph agentic analysis on current flight data.
    
    This endpoint:
    1. Fetches flight data from the specified provider
    2. Runs the multi-agent LangGraph workflow
    3. Returns disruption analysis, recommendations, and what-if scenarios
    4. Persists audit log and simulations to MongoDB
    
    Requires AGENTIC_ENABLED=true and OPENAI_API_KEY to be configured.
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agentic analysis is not enabled. Set AGENTIC_ENABLED=true in environment."
        )
    
    # Fetch flight data from provider
    selected_mode: ProviderMode = mode or settings.default_mode  # type: ignore
    provider = resolve_provider(selected_mode)
    
    try:
        flight_data = await provider.get_payload(airport.upper(), carrier.upper())
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch flight data: {str(exc)}"
        ) from exc

    if scenario:
        flight_data = apply_debug_scenario(flight_data, scenario)
    
    # Run agentic analysis
    try:
        result = await agentic_service.analyze_disruption(
            flight_data, engine=engine
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agentic analysis failed: {str(exc)}"
        ) from exc
    
    # Return combined response
    return {
        "airport": airport.upper(),
        "carrier": carrier.upper(),
        "mode": selected_mode,
        "engine": result.get("engine", settings.agentic_mode),
        "agentic_analysis": result,
        "original_data": {
            "stats": flight_data.get("stats"),
            "alerts": flight_data.get("alerts"),
        },
        "scenario": scenario,
    }


@router.get("/history")
async def get_analysis_history(
    airport: str = Query("HKG", description="IATA code of the station"),
    carrier: str = Query("CX", description="Airline designator"),
    limit: int = Query(10, description="Number of records to return", ge=1, le=50),
    engine: str | None = Query(
        None,
        description=f"Filter by agentic engine ({', '.join(sorted(AGENTIC_ENGINES))})",
    ),
) -> Dict[str, Any]:
    """Retrieve historical agentic analyses for an airport/carrier.
    
    Returns audit logs from previous disruption analyses, including:
    - Detection status
    - Risk assessments
    - Agent reasoning traces
    - Final action plans
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agentic analysis is not enabled."
        )
    
    try:
        analyses = await agentic_service.get_recent_analyses(
            airport.upper(), carrier.upper(), limit, engine=engine
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(exc)}"
        ) from exc
    
    return {
        "airport": airport.upper(),
        "carrier": carrier.upper(),
        "count": len(analyses),
        "analyses": analyses,
    }


@router.get("/simulations")
async def get_simulation_history(
    airport: str = Query("HKG", description="IATA code of the station"),
    carrier: str = Query("CX", description="Airline designator"),
    limit: int = Query(10, description="Number of records to return", ge=1, le=50),
    engine: str | None = Query(
        None,
        description=f"Filter by agentic engine ({', '.join(sorted(AGENTIC_ENGINES))})",
    ),
) -> Dict[str, Any]:
    """Retrieve historical what-if simulation results.
    
    Returns previous simulation scenarios including:
    - Risk scenarios (delay >3hr, crew unavailable, etc.)
    - Comparative outcomes
    - Cost/impact analyses
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agentic analysis is not enabled."
        )
    
    try:
        simulations = await agentic_service.get_simulation_history(
            airport.upper(), carrier.upper(), limit, engine=engine
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve simulations: {str(exc)}"
        ) from exc
    
    return {
        "airport": airport.upper(),
        "carrier": carrier.upper(),
        "count": len(simulations),
        "simulations": simulations,
    }


@router.get("/status")
async def get_agentic_status() -> Dict[str, Any]:
    """Check agentic system configuration and status.
    
    Returns:
        Configuration status including enabled state, LLM providers, etc.
    """
    provider_info = get_provider_info()
    
    return {
        "enabled": settings.agentic_enabled,
        "current_engine": settings.agentic_mode,
        "available_engines": sorted(AGENTIC_ENGINES),
        "current_provider": provider_info["current_provider"],
        "current_model": provider_info["current_model"],
        "temperature": provider_info["temperature"],
        "provider_configured": provider_info["provider_configured"],
        "mongo_configured": bool(settings.mongo_uri),
        "providers": provider_info["providers"],
    }


@router.get("/providers")
async def get_providers() -> Dict[str, Any]:
    """Get detailed information about all configured LLM providers.
    
    Returns:
        Comprehensive provider configuration and status
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agentic analysis is not enabled."
        )
    
    return get_provider_info()
