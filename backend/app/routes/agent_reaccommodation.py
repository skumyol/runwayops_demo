"""Agent-powered reaccommodation recommendations using LangGraph workflow.

This module provides AI-powered reaccommodation suggestions by invoking
the LangGraph multi-agent workflow on flight disruption data.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

# LLM errors are handled as generic exceptions
from ..config import settings
from ..services.agentic import agentic_service
from ..services import reaccommodation as data_service

router = APIRouter(
    prefix="/api/agent-reaccommodation", 
    tags=["agent-reaccommodation"]
)


@router.post("/analyze/{flight_number}")
async def analyze_flight_with_agents(
    flight_number: str,
    force_refresh: bool = Query(
        False, 
        description="Force new analysis even if cached result exists"
    ),
    engine: str | None = Query(
        None,
        description="Agent engine override (langgraph or apiv2)",
    ),
) -> dict[str, Any]:
    """Run LangGraph multi-agent analysis on a specific flight disruption.
    
    This endpoint:
    1. Fetches flight manifest, passengers, crew from MongoDB
    2. Runs LangGraph workflow (predictive → orchestrator → sub-agents → aggregator)
    3. Returns AI-powered recommendations including:
       - Risk assessment
       - Rebooking strategies
       - Financial estimates
       - Crew rotation needs
       - What-if scenarios
    
    Args:
        flight_number: Flight to analyze (e.g., CX888)
        force_refresh: Skip cache and run fresh analysis
        
    Returns:
        Complete agentic analysis with audit trail and recommendations
        
    Raises:
        HTTPException 503: Agentic system not enabled
        HTTPException 404: Flight not found
        HTTPException 500: Analysis failed
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agentic analysis is not enabled. Set AGENTIC_ENABLED=true in .env"
        )
    
    # Fetch flight data from MongoDB
    manifest = await data_service.fetch_manifest(flight_number)
    if not manifest:
        raise HTTPException(
            status_code=404,
            detail=f"Flight {flight_number} not found in database"
        )
    
    passengers_raw = await data_service.fetch_passengers_for_flight(flight_number)
    crew_raw = await data_service.fetch_crew_for_flight(flight_number)
    disruption = await data_service.fetch_disruption(manifest.disruptionId)
    
    # Build input data for LangGraph workflow
    input_data = {
        "airport": "HKG",  # Extract from flight if available
        "carrier": "CX",
        "flight_number": flight_number,
        "manifest": manifest.model_dump(),
        "passengers": passengers_raw,
        "crew": crew_raw,
        "disruption": disruption.model_dump() if disruption else None,
        "stats": {
            "totalPassengers": len(passengers_raw),
            "totalCrew": len(crew_raw),
            "affectedCount": manifest.summary.affectedCount,
        },
    }
    
    try:
        # Run LangGraph workflow through agentic service
        result = await agentic_service.analyze_disruption(
            input_data, engine=engine
        )
        
        return {
            "flightNumber": flight_number,
            "analysis": result,
            "metadata": {
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "timestamp": result.get("timestamp"),
                "engine": result.get("engine", settings.agentic_mode),
            },
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/suggestions/{flight_number}")
async def get_ai_suggestions(
    flight_number: str,
    passenger_pnr: str | None = Query(None, description="Filter for specific passenger"),
    engine: str | None = Query(
        None, description="Agent engine override (langgraph or apiv2)"
    ),
) -> dict[str, Any]:
    """Get AI-generated reaccommodation suggestions for a flight or passenger.
    
    This is a simplified endpoint that returns actionable suggestions
    extracted from the full agentic analysis.
    
    Args:
        flight_number: Flight to get suggestions for
        passenger_pnr: Optional PNR to get passenger-specific suggestions
        
    Returns:
        Simplified suggestions with recommended actions
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agentic analysis is not enabled"
        )
    
    # Get or create analysis
    manifest = await data_service.fetch_manifest(flight_number)
    if not manifest:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    passengers_raw = await data_service.fetch_passengers_for_flight(flight_number)
    crew_raw = await data_service.fetch_crew_for_flight(flight_number)
    disruption = await data_service.fetch_disruption(manifest.disruptionId)
    
    input_data = {
        "airport": "HKG",
        "carrier": "CX",
        "flight_number": flight_number,
        "manifest": manifest.model_dump(),
        "passengers": passengers_raw,
        "crew": crew_raw,
        "disruption": disruption.model_dump() if disruption else None,
    }
    
    try:
        result = await agentic_service.analyze_disruption(
            input_data, engine=engine
        )
        final_plan = result.get("final_plan", {})
        
        # Extract actionable suggestions
        rebooking = final_plan.get("rebooking_plan", {})
        risk = final_plan.get("risk_assessment", {})
        finance = final_plan.get("finance_estimate", {})
        
        suggestions = {
            "flightNumber": flight_number,
            "disruption_detected": result.get("disruption_detected", False),
            "recommended_action": final_plan.get("recommended_action"),
            "priority": final_plan.get("priority"),
            "confidence": final_plan.get("confidence"),
            "risk_level": risk.get("likelihood"),
            "estimated_cost": finance.get("total_estimate"),
            "rebooking_strategy": rebooking.get("strategy"),
            "affected_passengers": rebooking.get("affected_pax_count"),
            "what_if_scenarios": final_plan.get("what_if_scenarios", []),
            "reasoning": {
                "risk": risk.get("reasoning"),
                "rebooking": rebooking.get("reasoning"),
                "finance": finance.get("reasoning"),
            },
        }
        
        # Filter for specific passenger if requested
        if passenger_pnr:
            passenger = next(
                (p for p in passengers_raw if p.get("pnr") == passenger_pnr.upper()),
                None
            )
            if passenger:
                suggestions["passenger"] = {
                    "pnr": passenger.get("pnr"),
                    "name": passenger.get("name"),
                    "tier": passenger.get("tier"),
                    "specific_recommendation": _get_passenger_recommendation(
                        passenger, rebooking
                    ),
                }
        
        return suggestions
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


def _get_passenger_recommendation(
    passenger: dict[str, Any], 
    rebooking_plan: dict[str, Any]
) -> str:
    """Generate passenger-specific recommendation based on tier and context."""
    tier = passenger.get("tier", "Green")
    is_prm = passenger.get("isPRM", False)
    
    if tier in ["Diamond", "Gold"]:
        base = "Priority rebooking with lounge access and compensation"
    elif tier == "Silver":
        base = "Standard rebooking with meal vouchers"
    else:
        base = "Standard rebooking"
    
    if is_prm:
        base += " + special assistance pre-arranged"
    
    strategy = rebooking_plan.get("strategy", "")
    if "same-day" in strategy.lower():
        base += " on same-day alternative flight"
    elif "next-day" in strategy.lower():
        base += " on next available flight with hotel accommodation"
    
    return base


@router.get("/compare/{flight_number}")
async def compare_static_vs_ai(flight_number: str) -> dict[str, Any]:
    """Compare static MongoDB options vs AI-generated recommendations.
    
    Useful for seeing the difference between pre-computed options
    and real-time AI analysis.
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agentic analysis is not enabled"
        )
    
    manifest = await data_service.fetch_manifest(flight_number)
    if not manifest:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Get static options from MongoDB
    static_options = manifest.options
    
    # Get AI suggestions
    ai_result = await get_ai_suggestions(flight_number)
    
    return {
        "flightNumber": flight_number,
        "static": {
            "source": "MongoDB pre-generated",
            "count": len(static_options),
            "options": [opt.model_dump() for opt in static_options],
        },
        "ai_powered": {
            "source": f"LangGraph ({settings.llm_provider}/{settings.llm_model})",
            "suggestions": ai_result,
        },
        "comparison": {
            "static_is_deterministic": True,
            "ai_is_dynamic": True,
            "ai_includes_reasoning": True,
            "ai_includes_what_if": True,
        },
    }
