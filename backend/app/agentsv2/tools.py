"""Custom tools for ADK agents in the disruption workflow.

These tools implement domain-specific functionality for flight disruption
management, including predictive signals, rebooking, finance, and crew scheduling.
"""

import logging
import random
from typing import Any, Dict, List

from ..services.predictive_signals import compute_predictive_signals
from ..config import settings

logger = logging.getLogger(__name__)

# Import Amadeus tools conditionally
try:
    from .amadeus_tools import (
        search_alternative_flights_tool,
        search_hotels_tool,
        comprehensive_reaccommodation_tool,
    )
    AMADEUS_AVAILABLE = True
except ImportError:
    AMADEUS_AVAILABLE = False
    logger.warning("Amadeus tools not available - falling back to synthetic data")


# Tool decorator for ADK compatibility
# Note: ADK expects async functions for tools
async def predictive_signal_tool(
    airport: str,
    carrier: str,
    weather_score: float,
    aircraft_score: float,
    crew_score: float,
    payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compute predictive disruption signals from flight data.
    
    This tool analyzes weather, aircraft, and crew signals to determine
    disruption probability and generate risk assessment.
    
    Args:
        airport: Airport code (e.g., 'HKG')
        carrier: Carrier code (e.g., 'CX')
        weather_score: Weather risk score (0-1)
        aircraft_score: Aircraft condition score (0-1)
        crew_score: Crew availability score (0-1)
        
    Returns:
        Dictionary containing:
            - risk_probability: Overall disruption probability
            - disruption_detected: Boolean flag
            - signal_breakdown: Individual signal scores
            - likelihood: Risk category
    """
    if payload:
        # Copy so we do not mutate upstream state when we add fallbacks
        input_data = dict(payload)
        stats = dict(input_data.get("stats", {}) or {})
        stats.setdefault("weatherScore", weather_score)
        stats.setdefault("aircraftScore", aircraft_score)
        stats.setdefault("crewScore", crew_score)
        input_data["stats"] = stats
    else:
        input_data = {
            "airport": airport,
            "carrier": carrier,
            "stats": {
                "weatherScore": weather_score,
                "aircraftScore": aircraft_score,
                "crewScore": crew_score,
            },
        }
    
    result = compute_predictive_signals(input_data)
    
    logger.info(
        f"🎯 Predictive Tool: Risk={result['risk_probability']:.2%}, "
        f"Detected={result['disruption_detected']}"
    )
    
    return result


async def rebooking_tool(
    flight_id: str,
    pax_count: int,
    delay_minutes: int,
    vip_count: int = 0,
    disruption_type: str = "delay",
    origin: str = "HKG",
    destination: str = "LAX",
    departure_date: str = None
) -> Dict[str, Any]:
    """Generate passenger re-accommodation plan using Amadeus API or synthetic data.
    
    This tool creates rebooking strategies considering passenger count,
    VIP priority, delay duration, and hotel requirements. When Amadeus API
    credentials are configured, it uses real flight and hotel data.
    
    Args:
        flight_id: Flight identifier
        pax_count: Number of affected passengers
        delay_minutes: Expected delay duration
        vip_count: Number of VIP passengers
        disruption_type: Type of disruption (delay, cancellation, etc.)
        origin: Origin airport code (for Amadeus search)
        destination: Destination airport code (for Amadeus search)
        departure_date: Departure date in YYYY-MM-DD format
        
    Returns:
        Dictionary containing:
            - strategy: Rebooking strategy (same_day, next_day, etc.)
            - hotel_required: Whether hotel arrangements needed
            - vip_priority: VIP handling flag
            - estimated_pax: Number of affected passengers
            - actions: List of recommended actions
            - flight_options: Alternative flight options (if using Amadeus)
            - hotel_options: Hotel options (if using Amadeus)
            - data_source: 'amadeus' or 'synthetic'
    """
    # Check if Amadeus is available and configured
    use_amadeus = (
        AMADEUS_AVAILABLE 
        and settings.amadeus_client_id 
        and settings.amadeus_client_secret
    )
    
    if use_amadeus and departure_date:
        logger.info("🌍 Using Amadeus API for real flight/hotel data")
        
        try:
            # Use comprehensive Amadeus re-accommodation tool
            amadeus_result = await comprehensive_reaccommodation_tool(
                origin=origin,
                destination=destination,
                original_departure_date=departure_date,
                passenger_count=pax_count,
                vip_count=vip_count,
                delay_minutes=delay_minutes
            )
            
            # Merge Amadeus data with standard response
            result = {
                "flight_id": flight_id,
                "strategy": amadeus_result["recommended_plan"]["strategy"],
                "hotel_required": amadeus_result.get("needs_hotel", False),
                "vip_priority": vip_count > 0,
                "estimated_pax": pax_count,
                "vip_count": vip_count,
                "delay_minutes": delay_minutes,
                "actions": amadeus_result["recommended_plan"]["actions"],
                "flight_options": amadeus_result["flight_options"],
                "hotel_options": amadeus_result["hotel_options"],
                "total_cost_estimate": amadeus_result["total_cost_estimate"],
                "data_source": "amadeus",
                "reasoning": amadeus_result.get("reasoning", "")
            }
            
            logger.info(
                f"✈️  Rebooking Tool (Amadeus): {result['strategy']} for {pax_count} pax, "
                f"Found {amadeus_result['flight_options']['count']} flights, "
                f"Cost: ${amadeus_result['total_cost_estimate']:,.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Amadeus API failed, falling back to synthetic: {e}")
            # Fall through to synthetic data
    
    # Synthetic data fallback
    logger.info("🔧 Using synthetic data for rebooking")
    
    # Determine strategy based on delay
    if delay_minutes > 180:
        strategy = "next_day_alternate"
        hotel_required = True
    elif delay_minutes > 60:
        strategy = "same_day_alternate"
        hotel_required = delay_minutes > 180
    else:
        strategy = "monitor_and_assess"
        hotel_required = False
    
    actions = []
    if hotel_required:
        actions.append(f"Book hotels for {pax_count} passengers")
        actions.append("Arrange meal vouchers")
    
    if vip_count > 0:
        actions.append(f"Prioritize {vip_count} VIP passengers for rebooking")
    
    actions.append(f"Search alternative flights for {pax_count} passengers")
    actions.append("Notify passengers via SMS/email")
    
    result = {
        "flight_id": flight_id,
        "strategy": strategy,
        "hotel_required": hotel_required,
        "vip_priority": vip_count > 0,
        "estimated_pax": pax_count,
        "vip_count": vip_count,
        "delay_minutes": delay_minutes,
        "actions": actions,
        "data_source": "synthetic",
        "reasoning": (
            f"Based on {delay_minutes}min delay with {pax_count} pax "
            f"(including {vip_count} VIPs), recommend {strategy} strategy"
        )
    }
    
    logger.info(
        f"✈️  Rebooking Tool (Synthetic): {strategy} for {pax_count} pax, "
        f"Hotel={hotel_required}"
    )
    
    return result


async def finance_tool(
    pax_count: int,
    delay_minutes: int,
    hotel_required: bool,
    flight_distance: str = "short"
) -> Dict[str, Any]:
    """Calculate financial impact of disruption.
    
    Estimates compensation, hotel/meal costs, and operational costs
    based on EU261/HKCAD regulations.
    
    Args:
        pax_count: Number of affected passengers
        delay_minutes: Delay duration
        hotel_required: Whether hotel costs apply
        flight_distance: Flight category (short, medium, long)
        
    Returns:
        Dictionary containing:
            - compensation_usd: Passenger compensation costs
            - hotel_meals_usd: Hotel and meal costs
            - operational_usd: Operational overhead costs
            - total_usd: Total estimated cost
            - breakdown: Itemized cost breakdown
    """
    # Compensation based on EU261/HKCAD
    if delay_minutes >= 180:
        if flight_distance == "long":
            per_pax_comp = 600
        elif flight_distance == "medium":
            per_pax_comp = 400
        else:
            per_pax_comp = 250
    elif delay_minutes >= 120:
        per_pax_comp = 125
    else:
        per_pax_comp = 0
    
    compensation_usd = pax_count * per_pax_comp
    
    # Hotel and meals
    hotel_meals_usd = 0
    if hotel_required:
        hotel_per_pax = 150  # Average hotel + meals
        hotel_meals_usd = pax_count * hotel_per_pax
    
    # Operational costs (fuel, crew overtime, etc.)
    operational_usd = random.randint(10000, 30000)
    
    total_usd = compensation_usd + hotel_meals_usd + operational_usd
    
    breakdown = [
        f"Compensation: ${compensation_usd:,} ({pax_count} pax × ${per_pax_comp})",
        f"Hotel/Meals: ${hotel_meals_usd:,}",
        f"Operational: ${operational_usd:,}"
    ]
    
    result = {
        "compensation_usd": compensation_usd,
        "hotel_meals_usd": hotel_meals_usd,
        "operational_usd": operational_usd,
        "total_usd": total_usd,
        "breakdown": breakdown,
        "reasoning": f"Total estimated impact: ${total_usd:,}"
    }
    
    logger.info(f"💰 Finance Tool: Total=${total_usd:,}")
    
    return result


async def crew_scheduling_tool(
    flight_count: int,
    delay_minutes: int,
    crew_available: int = 10
) -> Dict[str, Any]:
    """Assess crew scheduling impacts and requirements.
    
    Evaluates crew duty time limits, rest requirements, and backup needs.
    
    Args:
        flight_count: Number of affected flights
        delay_minutes: Expected delay
        crew_available: Number of backup crew available
        
    Returns:
        Dictionary containing:
            - crew_changes_needed: Whether crew changes required
            - backup_crew_required: Number of backup crew needed
            - regulatory_issues: List of compliance concerns
            - actions: Recommended crew actions
    """
    # Determine if crew changes needed based on duty limits
    crew_changes_needed = delay_minutes > 120
    
    if crew_changes_needed:
        backup_crew_required = min(flight_count, crew_available)
        regulatory_issues = [
            "Crew duty time approaching limit",
            "Rest requirements must be maintained"
        ]
        actions = [
            f"Assign {backup_crew_required} backup crew members",
            "Monitor crew duty times",
            "Ensure regulatory compliance with rest periods"
        ]
    else:
        backup_crew_required = 0
        regulatory_issues = []
        actions = ["Monitor crew duty times", "Keep backup crew on standby"]
    
    result = {
        "crew_changes_needed": crew_changes_needed,
        "backup_crew_required": backup_crew_required,
        "crew_available": crew_available,
        "regulatory_issues": regulatory_issues,
        "actions": actions,
        "reasoning": (
            f"Delay of {delay_minutes}min requires "
            f"{'crew changes' if crew_changes_needed else 'monitoring only'}"
        )
    }
    
    logger.info(
        f"👥 Crew Tool: Changes={crew_changes_needed}, "
        f"Backup={backup_crew_required}"
    )
    
    return result


# Tool registry for ADK
# These will be registered with agents as needed
DISRUPTION_TOOLS = {
    "predictive_signal_tool": predictive_signal_tool,
    "rebooking_tool": rebooking_tool,
    "finance_tool": finance_tool,
    "crew_scheduling_tool": crew_scheduling_tool,
}

# Add Amadeus tools if available
if AMADEUS_AVAILABLE:
    DISRUPTION_TOOLS.update({
        "search_alternative_flights": search_alternative_flights_tool,
        "search_hotels": search_hotels_tool,
        "comprehensive_reaccommodation": comprehensive_reaccommodation_tool,
    })
