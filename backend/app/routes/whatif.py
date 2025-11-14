"""What-if scenario analysis endpoint.

Allows users to simulate different scenarios and see predicted outcomes
without affecting actual flight data.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config import settings
from ..providers import ProviderMode, resolve_provider
from ..services.agentic import agentic_service
from ..services.predictive_monitor import get_predictive_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatif", tags=["what-if"])


class WhatIfScenario(BaseModel):
    """What-if scenario parameters."""
    
    flight_number: str = Field(description="Flight to analyze")
    
    # Scenario modifications
    delay_minutes: int | None = Field(
        None,
        description="Simulate additional delay (minutes)"
    )
    weather_impact: Literal["none", "minor", "moderate", "severe"] | None = Field(
        None,
        description="Simulate weather conditions"
    )
    crew_unavailable: int | None = Field(
        None,
        description="Number of crew members unavailable"
    )
    aircraft_issue: bool | None = Field(
        None,
        description="Simulate aircraft maintenance issue"
    )
    passenger_count_change: int | None = Field(
        None,
        description="Adjust passenger count (+/-)"
    )
    connection_pressure: Literal["low", "medium", "high"] | None = Field(
        None,
        description="Simulate connection pressure level"
    )


@router.post("/analyze")
async def analyze_whatif_scenario(
    scenario: WhatIfScenario,
    airport: str = Query("HKG", description="IATA code"),
    carrier: str = Query("CX", description="Airline designator"),
    mode: ProviderMode | None = Query(
        None,
        description="Data source (defaults to FLIGHT_MONITOR_MODE)"
    ),
) -> Dict[str, Any]:
    """
    Run a what-if scenario analysis.
    
    This endpoint:
    1. Fetches current flight data
    2. Applies scenario modifications
    3. Runs agent analysis with modified data
    4. Returns predicted outcome
    
    **Does not affect actual flight data!**
    """
    logger.info("=" * 80)
    logger.info(f"🔮 WHAT-IF SCENARIO: {scenario.flight_number}")
    logger.info("=" * 80)
    
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="What-if analysis requires AGENTIC_ENABLED=true"
        )
    
    # Fetch current flight data
    selected_mode: ProviderMode = mode or settings.default_mode  # type: ignore
    provider = resolve_provider(selected_mode)
    
    try:
        payload = await provider.get_payload(airport.upper(), carrier.upper())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch flight data: {str(e)}"
        )
    
    # Find the specific flight
    flights = payload.get("flights", [])
    flight = next(
        (f for f in flights if f.get("flightNumber") == scenario.flight_number),
        None
    )
    
    if not flight:
        raise HTTPException(
            status_code=404,
            detail=f"Flight {scenario.flight_number} not found"
        )
    
    logger.info(f"📊 Baseline: {flight.get('statusCategory')} - "
                f"{flight.get('delayMinutes', 0)}min delay")
    
    # Apply scenario modifications
    modified_payload = _apply_scenario_modifications(
        payload.copy(),
        flight,
        scenario
    )
    
    logger.info("🎭 Scenario modifications applied:")
    if scenario.delay_minutes:
        logger.info(f"   ⏱️  Additional delay: +{scenario.delay_minutes}min")
    if scenario.weather_impact:
        logger.info(f"   🌧️  Weather: {scenario.weather_impact}")
    if scenario.crew_unavailable:
        logger.info(f"   👥 Crew unavailable: {scenario.crew_unavailable}")
    if scenario.aircraft_issue:
        logger.info(f"   ✈️  Aircraft issue: YES")
    if scenario.passenger_count_change:
        logger.info(f"   🧳 Passenger count: {scenario.passenger_count_change:+d}")
    if scenario.connection_pressure:
        logger.info(f"   🔗 Connection pressure: {scenario.connection_pressure}")
    
    # Run agent analysis on modified data
    logger.info("🚀 Running agent analysis on scenario...")
    
    try:
        analysis = await agentic_service.analyze_disruption(
            modified_payload,
            engine="apiv2"
        )
        
        logger.info("✅ What-if analysis complete")
        
        return {
            "scenario": scenario.model_dump(),
            "baseline": {
                "statusCategory": flight.get("statusCategory"),
                "delayMinutes": flight.get("delayMinutes", 0),
                "paxImpacted": flight.get("paxImpacted", 0),
            },
            "predicted_outcome": {
                "disruption_detected": analysis.get("disruption_detected", False),
                "risk_assessment": analysis.get("risk_assessment", {}),
                "final_plan": analysis.get("final_plan", {}),
                "signal_breakdown": analysis.get("signal_breakdown", {}),
            },
            "comparison": _generate_comparison(flight, analysis),
            "timestamp": analysis.get("timestamp"),
        }
        
    except Exception as e:
        logger.error(f"❌ What-if analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/predict/{flight_number}")
async def predict_flight_disruption(
    flight_number: str,
    airport: str = Query("HKG"),
    carrier: str = Query("CX"),
    mode: ProviderMode | None = Query(None),
    force: bool = Query(
        False,
        description="Force prediction even if disruption exists"
    ),
) -> Dict[str, Any]:
    """
    Get or compute disruption prediction for a specific flight.
    
    Automatically skips prediction if disruption has already occurred
    (unless force=true).
    """
    logger.info(f"🔮 Prediction request for {flight_number}")
    
    # Fetch flight data
    selected_mode: ProviderMode = mode or settings.default_mode  # type: ignore
    provider = resolve_provider(selected_mode)
    
    try:
        payload = await provider.get_payload(airport.upper(), carrier.upper())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch flight data: {str(e)}"
        )
    
    # Find flight
    flights = payload.get("flights", [])
    flight = next(
        (f for f in flights if f.get("flightNumber") == flight_number),
        None
    )
    
    if not flight:
        raise HTTPException(
            status_code=404,
            detail=f"Flight {flight_number} not found"
        )
    
    # Prepare flight data for prediction
    flight_data = {
        "flight_number": flight_number,
        "airport": airport,
        "carrier": carrier,
        "stats": payload.get("stats", {}),
        "flights": [flight],
        "alerts": payload.get("alerts", []),
        "disruption": flight.get("irregularOps"),  # Current IROP if any
    }
    
    # Run prediction
    monitor = get_predictive_monitor()
    result = await monitor.predict_disruption(flight_data, force=force)
    
    return result


def _apply_scenario_modifications(
    payload: Dict[str, Any],
    flight: Dict[str, Any],
    scenario: WhatIfScenario
) -> Dict[str, Any]:
    """Apply what-if scenario modifications to payload."""
    
    # Find flight in payload
    flight_index = next(
        (i for i, f in enumerate(payload["flights"])
         if f.get("flightNumber") == scenario.flight_number),
        None
    )
    
    if flight_index is None:
        return payload
    
    modified_flight = payload["flights"][flight_index].copy()
    
    # Initialize stats if not present
    if "stats" not in payload:
        payload["stats"] = {
            "weatherScore": 0.1,
            "aircraftScore": 0.1,
            "crewScore": 0.1,
            "delayed": 0,
            "critical": 0,
        }
    
    # Apply delay
    if scenario.delay_minutes:
        current_delay = modified_flight.get("delayMinutes", 0)
        modified_flight["delayMinutes"] = current_delay + scenario.delay_minutes
        
        # Update status if delay is significant
        total_delay = current_delay + scenario.delay_minutes
        if total_delay >= 60:
            modified_flight["statusCategory"] = "critical"
            payload["stats"]["critical"] = payload["stats"].get("critical", 0) + 1
        elif total_delay >= 20:
            modified_flight["statusCategory"] = "warning"
            payload["stats"]["delayed"] = payload["stats"].get("delayed", 0) + 1
    
    # Apply weather impact - UPDATE WEATHER SCORE
    if scenario.weather_impact and scenario.weather_impact != "none":
        weather_score_map = {
            "minor": 0.3,
            "moderate": 0.6,
            "severe": 0.9
        }
        payload["stats"]["weatherScore"] = weather_score_map[scenario.weather_impact]
        
        payload.setdefault("alerts", []).append({
            "level": "critical" if scenario.weather_impact == "severe" else "warning",
            "message": f"Weather: {scenario.weather_impact} conditions",
            "flightNumber": scenario.flight_number,
        })
    
    # Apply crew issues - UPDATE CREW SCORE
    if scenario.crew_unavailable:
        modified_flight["crewReady"] = False
        # Higher crew unavailable = higher score (more risk)
        payload["stats"]["crewScore"] = min(0.9, scenario.crew_unavailable * 0.15)
        
        if "irregularOps" not in modified_flight:
            modified_flight["irregularOps"] = {"reason": "", "actions": []}
        modified_flight["irregularOps"]["reason"] += f" | {scenario.crew_unavailable} crew unavailable"
    
    # Apply aircraft issue - UPDATE AIRCRAFT SCORE
    if scenario.aircraft_issue:
        modified_flight["aircraftReady"] = False
        payload["stats"]["aircraftScore"] = 0.8  # High aircraft risk
        
        if "irregularOps" not in modified_flight:
            modified_flight["irregularOps"] = {"reason": "", "actions": []}
        modified_flight["irregularOps"]["reason"] += " | Aircraft maintenance required"
    
    # Apply passenger count change
    if scenario.passenger_count_change:
        modified_flight["paxCount"] = max(
            0,
            modified_flight.get("paxCount", 0) + scenario.passenger_count_change
        )
    
    # Apply connection pressure
    if scenario.connection_pressure:
        pressure_map = {"low": 5, "medium": 15, "high": 30}
        modified_flight.setdefault("connections", {})["tight"] = pressure_map[scenario.connection_pressure]
        # High connection pressure increases overall risk
        if scenario.connection_pressure == "high":
            payload["stats"]["weatherScore"] = max(
                payload["stats"].get("weatherScore", 0),
                0.4  # Bump up weather score as proxy for time pressure
            )
    
    payload["flights"][flight_index] = modified_flight
    
    logger.info(f"📊 Modified stats scores:")
    logger.info(f"   Weather: {payload['stats'].get('weatherScore', 0):.2f}")
    logger.info(f"   Aircraft: {payload['stats'].get('aircraftScore', 0):.2f}")
    logger.info(f"   Crew: {payload['stats'].get('crewScore', 0):.2f}")
    
    return payload


def _generate_comparison(
    baseline_flight: Dict[str, Any],
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate comparison between baseline and predicted scenario."""
    
    final_plan = analysis.get("final_plan", {})
    
    return {
        "risk_change": {
            "baseline": baseline_flight.get("statusCategory", "normal"),
            "predicted": final_plan.get("priority", "unknown"),
        },
        "financial_impact": final_plan.get("finance_estimate", {}).get("total_usd", 0),
        "passengers_affected": final_plan.get("rebooking_plan", {}).get("affected_pax_count", 0),
        "recommended_actions": final_plan.get("rebooking_plan", {}).get("actions", [])[:3],
    }
