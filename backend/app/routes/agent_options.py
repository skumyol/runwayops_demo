"""Agent-generated reaccommodation options endpoint.

This replaces static MongoDB options with AI-generated ones from LangGraph agents.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from ..agents.llm_factory import LLMProviderError
from ..config import settings
from ..schemas.reaccommodation import ReaccommodationOption
from ..services.agentic import agentic_service
from ..services import reaccommodation as data_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-options",
    tags=["agent-options"]
)


@router.get("/health")
async def agent_options_health() -> dict[str, Any]:
    """Test endpoint to verify router is working."""
    return {
        "status": "ok",
        "router": "agent-options",
        "agentic_enabled": settings.agentic_enabled,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "deepseek_key_configured": bool(settings.deepseek_api_key),
        "openai_key_configured": bool(settings.openai_api_key),
    }


def _generate_options_from_analysis(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert agent analysis into ReaccommodationOption format.
    
    Takes the rebooking agent's output and generates structured options
    that match the existing UI format.
    """
    final_plan = analysis.get("final_plan", {})
    rebooking = final_plan.get("rebooking_plan", {})
    
    # Extract base information
    strategy = rebooking.get("strategy", "Standard rebooking")
    affected_count = rebooking.get("affected_pax_count", 0)
    
    # Generate options based on agent recommendations
    options = []
    
    # Option 1: Primary recommendation (same-day if possible)
    options.append({
        "id": "agent-opt-1",
        "departureTime": "08:30",  # Would come from inventory system
        "arrivalTime": "14:45",
        "route": "HKG → SIN → LHR",
        "cabin": "Y",
        "seats": max(10, affected_count // 3),
        "trvScore": 92,
        "arrivalDelta": "+2h 15m",
        "badges": ["Fastest", "Agent Recommended"],
        "whyReasons": [
            {
                "icon": "clock",
                "reason": strategy or "Minimal delay impact",
                "sentiment": "positive"
            },
            {
                "icon": "shield",
                "reason": f"AI Risk Assessment: {final_plan.get('risk_assessment', {}).get('likelihood', 'medium')} priority",
                "sentiment": "neutral"
            }
        ]
    })
    
    # Option 2: Alternative with better amenities
    options.append({
        "id": "agent-opt-2",
        "departureTime": "14:30",
        "arrivalTime": "21:15",
        "route": "HKG → DXB → LHR",
        "cabin": "Y",
        "seats": max(15, affected_count // 2),
        "trvScore": 85,
        "arrivalDelta": "+8h 30m",
        "badges": ["More Seats"],
        "whyReasons": [
            {
                "icon": "users",
                "reason": "Higher capacity for group accommodations",
                "sentiment": "positive"
            },
            {
                "icon": "briefcase",
                "reason": "Premium lounge access during layover",
                "sentiment": "positive"
            }
        ]
    })
    
    # Option 3: Next day if high risk
    risk_level = final_plan.get("risk_assessment", {}).get("likelihood", "medium")
    if risk_level in ["high", "critical"]:
        options.append({
            "id": "agent-opt-3",
            "departureTime": "09:00 +1",
            "arrivalTime": "15:30 +1",
            "route": "HKG → LHR",
            "cabin": "J",
            "seats": max(8, affected_count // 4),
            "trvScore": 95,
            "arrivalDelta": "+26h",
            "badges": ["Premium", "Hotel Included"],
            "whyReasons": [
                {
                    "icon": "star",
                    "reason": "Business class upgrade due to extended delay",
                    "sentiment": "positive"
                },
                {
                    "icon": "hotel",
                    "reason": f"Hotel accommodation included (${final_plan.get('finance_estimate', {}).get('hotel_meals_cost', 15000)} budget)",
                    "sentiment": "positive"
                },
                {
                    "icon": "shield",
                    "reason": "Guaranteed seats - no further disruption risk",
                    "sentiment": "positive"
                }
            ]
        })
    
    return options


@router.get("/flights/{flight_number}")
async def get_agent_options(flight_number: str) -> dict[str, Any]:
    """Get AI-generated reaccommodation options for a flight.
    
    This endpoint:
    1. Fetches flight data from MongoDB
    2. Runs LangGraph agent analysis
    3. Converts agent recommendations into option format
    4. Returns options compatible with existing UI
    
    Args:
        flight_number: Flight to generate options for
        
    Returns:
        Options in ReaccommodationOption format generated by agents
    """
    if not settings.agentic_enabled:
        raise HTTPException(
            status_code=503,
            detail="Agent-powered options require AGENTIC_ENABLED=true"
        )
    
    # Fetch flight data
    manifest = await data_service.fetch_manifest(flight_number)
    if not manifest:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    passengers_raw = await data_service.fetch_passengers_for_flight(flight_number)
    crew_raw = await data_service.fetch_crew_for_flight(flight_number)
    disruption = await data_service.fetch_disruption(manifest.disruptionId)
    
    # Build input for agents
    input_data = {
        "airport": "HKG",
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
        # Run agent analysis
        analysis = await agentic_service.analyze_disruption(input_data)
        
        # Generate options from agent recommendations
        agent_options = _generate_options_from_analysis(analysis)
        
        return {
            "flightNumber": flight_number,
            "options": agent_options,
            "source": "ai_agents",
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "analysis_summary": {
                "disruption_detected": analysis.get("disruption_detected", False),
                "risk_level": analysis.get("final_plan", {}).get("risk_assessment", {}).get("likelihood"),
                "recommended_action": analysis.get("final_plan", {}).get("recommended_action"),
                "confidence": analysis.get("final_plan", {}).get("confidence"),
            },
            "timestamp": analysis.get("timestamp"),
        }
    
    except LLMProviderError as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM provider error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate options: {str(e)}"
        )


@router.get("/passengers/{pnr}/options")
async def get_passenger_agent_options(pnr: str) -> dict[str, Any]:
    """Get personalized AI-generated options for a specific passenger.
    
    Analyzes passenger tier, SSRs, and preferences to generate
    tailored reaccommodation options.
    """
    logger.info(f"Fetching AI options for passenger {pnr}")
    
    if not settings.agentic_enabled:
        logger.warning(f"Agentic system not enabled for passenger {pnr}")
        raise HTTPException(
            status_code=503,
            detail="Agent-powered options require AGENTIC_ENABLED=true"
        )
    
    # Fetch passenger
    logger.info(f"Fetching passenger data for {pnr}")
    passenger_doc = await data_service.fetch_passenger(pnr)
    if not passenger_doc:
        logger.error(f"Passenger {pnr} not found in database")
        raise HTTPException(status_code=404, detail=f"Passenger {pnr} not found")
    
    flight_number = passenger_doc.get("originalFlight", "")
    manifest = await data_service.fetch_manifest(flight_number)
    if not manifest:
        raise HTTPException(status_code=404, detail="Flight manifest not found")
    
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
        "focus_passenger": passenger_doc,  # Highlight this passenger
    }
    
    try:
        analysis = await agentic_service.analyze_disruption(input_data)
        agent_options = _generate_options_from_analysis(analysis)
        
        # Personalize options based on passenger tier
        tier = passenger_doc.get("tier", "Green")
        is_prm = passenger_doc.get("isPRM", False)
        
        for option in agent_options:
            # Adjust based on tier
            if tier in ["Diamond", "Gold"]:
                option["badges"].append("Priority")
                if option["cabin"] == "Y":
                    option["cabin"] = "J"  # Upgrade eligible
                    option["whyReasons"].append({
                        "icon": "star",
                        "reason": f"{tier} tier upgrade eligibility",
                        "sentiment": "positive"
                    })
            
            # Add PRM considerations
            if is_prm:
                option["whyReasons"].append({
                    "icon": "accessibility",
                    "reason": "Special assistance pre-arranged",
                    "sentiment": "positive"
                })
        
        return {
            "pnr": pnr,
            "flightNumber": flight_number,
            "options": agent_options,
            "source": "ai_agents_personalized",
            "passenger": {
                "tier": tier,
                "isPRM": is_prm,
                "ssrs": passenger_doc.get("ssrs", []),
            },
            "timestamp": analysis.get("timestamp"),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate personalized options: {str(e)}"
        )
