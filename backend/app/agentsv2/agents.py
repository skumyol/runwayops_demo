"""ADK agent definitions for flight disruption management.

This module defines all agents in the disruption workflow using Google's
Agent Development Kit (ADK). Agents are organized hierarchically with
specialized roles.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .state import DisruptionState, log_reasoning
from .tools import (
    predictive_signal_tool,
    rebooking_tool,
    finance_tool,
    crew_scheduling_tool,
)


logger = logging.getLogger(__name__)


# Note: These are placeholder agent definitions
# The actual ADK imports will be:
# from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
# from google.adk.tools import Tool


class PredictiveAgent:
    """Predictive agent for disruption detection using signals.
    
    This agent analyzes weather, aircraft, and crew signals to detect
    potential disruptions before they occur.
    """
    
    def __init__(self):
        self.name = "PredictiveAgent"
        # In real ADK, this would be:
        # self.agent = LlmAgent(
        #     name="predictive_agent",
        #     model="gemini-2.5-flash",
        #     instruction="Analyze flight signals and detect disruptions",
        #     tools=[predictive_signal_tool]
        # )
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Execute predictive analysis on flight data.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with risk assessment
        """
        logger.info("=" * 80)
        logger.info("🧠 PREDICTIVE AGENT (ADK): Starting disruption analysis...")
        logger.info("=" * 80)
        
        input_data = state.input_data
        stats = input_data.get("stats", {})
        
        # Call predictive tool
        result = await predictive_signal_tool(
            airport=input_data.get("airport", "HKG"),
            carrier=input_data.get("carrier", "CX"),
            weather_score=stats.get("weatherScore", 0.5),
            aircraft_score=stats.get("aircraftScore", 0.5),
            crew_score=stats.get("crewScore", 0.5)
        )
        
        logger.info(
            f"🎯 Risk Probability: {result['risk_probability']:.2%} | "
            f"Disruption: {'DETECTED ✓' if result['disruption_detected'] else 'NOT DETECTED ✗'}"
        )
        
        state.disruption_detected = result["disruption_detected"]
        state.risk_assessment = result
        state.signal_breakdown = result.get("signal_breakdown", {})
        
        state = log_reasoning(state, self.name, input_data, result)
        
        return state


class OrchestratorAgent:
    """Orchestrator agent for coordinating disruption response.
    
    This LLM-powered agent analyzes disruptions, creates action plans,
    and simulates what-if scenarios.
    """
    
    def __init__(self):
        self.name = "OrchestratorAgent"
        # In real ADK:
        # self.agent = LlmAgent(
        #     name="orchestrator",
        #     model="gemini-2.5-flash",
        #     instruction=ORCHESTRATOR_PROMPT
        # )
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Coordinate disruption response strategy.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with orchestration plan and scenarios
        """
        logger.info("🎯 ORCHESTRATOR AGENT (ADK): Coordinating response...")
        
        # Simulated orchestrator logic
        # In production, this would invoke LLM with detailed prompt
        risk = state.risk_assessment
        
        output = {
            "requires_intervention": state.disruption_detected,
            "severity": self._calculate_severity(risk.get("risk_probability", 0)),
            "main_plan": {
                "description": "Coordinate multi-agent response to disruption",
                "priority_actions": [
                    "Assess passenger impact",
                    "Calculate financial implications",
                    "Review crew availability"
                ]
            },
            "what_if_scenarios": [
                {
                    "scenario": "delay_3hr",
                    "plan": {
                        "description": "Extended delay requiring hotels",
                        "actions": ["Book hotels", "Arrange meals", "Compensate passengers"]
                    }
                },
                {
                    "scenario": "crew_unavailable",
                    "plan": {
                        "description": "Crew duty limit exceeded",
                        "actions": ["Assign backup crew", "Reschedule flights"]
                    }
                }
            ],
            "reasoning": f"Risk probability at {risk.get('risk_probability', 0):.2%}"
        }
        
        logger.info(
            f"⚡ Decision: Intervention={'Yes' if output['requires_intervention'] else 'No'}, "
            f"Severity={output['severity']}"
        )
        
        state.simulation_results = output.get("what_if_scenarios", [])
        state = log_reasoning(state, self.name, {"risk": risk}, output)
        
        return state
    
    def _calculate_severity(self, risk_prob: float) -> str:
        """Calculate severity level from risk probability."""
        if risk_prob > 0.8:
            return "critical"
        elif risk_prob > 0.6:
            return "high"
        elif risk_prob > 0.4:
            return "medium"
        else:
            return "low"


class RiskAgent:
    """Risk assessment specialist agent."""
    
    def __init__(self):
        self.name = "RiskAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Assess disruption risk in detail.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with enhanced risk assessment
        """
        logger.info("⚠️  RISK AGENT (ADK): Assessing likelihood and impact...")
        
        risk_data = state.risk_assessment
        
        # Enhanced risk assessment
        result = {
            "likelihood": risk_data.get("risk_probability", 0.75),
            "duration_minutes": self._estimate_duration(risk_data),
            "pax_impact": self._assess_pax_impact(risk_data),
            "regulatory_risk": self._assess_regulatory_risk(risk_data),
            "reasoning": "Detailed risk assessment based on signals"
        }
        
        # Update state risk assessment with enhanced data
        state.risk_assessment.update(result)
        state = log_reasoning(state, self.name, risk_data, result)
        
        logger.info(
            f"📊 Risk: Likelihood={result['likelihood']:.2%}, "
            f"Duration={result['duration_minutes']}min, Impact={result['pax_impact']}"
        )
        
        return state
    
    def _estimate_duration(self, risk_data: Dict) -> int:
        """Estimate disruption duration from risk data."""
        risk_prob = risk_data.get("risk_probability", 0.5)
        if risk_prob > 0.8:
            return 240  # 4 hours
        elif risk_prob > 0.6:
            return 180  # 3 hours
        else:
            return 120  # 2 hours
    
    def _assess_pax_impact(self, risk_data: Dict) -> str:
        """Assess passenger impact severity."""
        risk_prob = risk_data.get("risk_probability", 0.5)
        if risk_prob > 0.7:
            return "high"
        elif risk_prob > 0.5:
            return "medium"
        else:
            return "low"
    
    def _assess_regulatory_risk(self, risk_data: Dict) -> str:
        """Assess regulatory compliance risk."""
        risk_prob = risk_data.get("risk_probability", 0.5)
        if risk_prob > 0.7:
            return "EU261/HKCAD compensation required"
        else:
            return "Monitor for compensation thresholds"


class RebookingAgent:
    """Passenger re-accommodation specialist agent."""
    
    def __init__(self):
        self.name = "RebookingAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Create passenger re-accommodation plan.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with rebooking plan
        """
        logger.info("✈️  REBOOKING AGENT (ADK): Planning re-accommodation...")
        
        input_data = state.input_data
        flights = input_data.get("flights", [])
        risk = state.risk_assessment
        
        # Find critical flights
        critical_flights = [f for f in flights if f.get("statusCategory") == "critical"]
        
        # Estimate passenger count
        pax_count = input_data.get("stats", {}).get("paxImpacted", 200)
        delay_minutes = risk.get("duration_minutes", 120)
        
        # Extract flight details for Amadeus API
        origin = input_data.get("airport", "HKG")
        
        # Try to extract destination from first critical flight
        destination = "LAX"  # Default
        departure_date = None
        
        if critical_flights:
            first_flight = critical_flights[0]
            # Try to extract destination from flight data
            if "route" in first_flight:
                destination = first_flight["route"].split("-")[-1].strip()
            elif "destination" in first_flight:
                destination = first_flight["destination"]
            
            # Try to extract departure date
            if "scheduledDeparture" in first_flight:
                # Parse date from ISO format
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(first_flight["scheduledDeparture"].replace("Z", "+00:00"))
                    departure_date = dt.strftime("%Y-%m-%d")
                except:
                    pass
        
        # Use rebooking tool with flight details
        result = await rebooking_tool(
            flight_id=critical_flights[0].get("id", "CX888") if critical_flights else "UNKNOWN",
            pax_count=pax_count,
            delay_minutes=delay_minutes,
            vip_count=int(pax_count * 0.1),  # Assume 10% VIPs
            disruption_type="delay",
            origin=origin,
            destination=destination,
            departure_date=departure_date
        )
        
        state.rebooking_plan = result
        state = log_reasoning(state, self.name, {"pax_count": pax_count}, result)
        
        logger.info(
            f"🎫 Rebooking: {result['strategy']}, "
            f"Hotel={result['hotel_required']}, PAX={pax_count}"
        )
        
        return state


class FinanceAgent:
    """Financial impact assessment agent."""
    
    def __init__(self):
        self.name = "FinanceAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Calculate financial impact of disruption.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with finance estimate
        """
        logger.info("💰 FINANCE AGENT (ADK): Calculating costs...")
        
        rebooking = state.rebooking_plan
        risk = state.risk_assessment
        
        pax_count = rebooking.get("estimated_pax", 200)
        delay_minutes = risk.get("duration_minutes", 120)
        hotel_required = rebooking.get("hotel_required", False)
        
        # Use finance tool
        result = await finance_tool(
            pax_count=pax_count,
            delay_minutes=delay_minutes,
            hotel_required=hotel_required,
            flight_distance="medium"
        )
        
        state.finance_estimate = result
        state = log_reasoning(state, self.name, {"pax_count": pax_count}, result)
        
        logger.info(f"💵 Total Cost: ${result['total_usd']:,}")
        
        return state


class CrewAgent:
    """Crew scheduling and management agent."""
    
    def __init__(self):
        self.name = "CrewAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Assess crew scheduling impacts.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with crew rotation plan
        """
        logger.info("👥 CREW AGENT (ADK): Managing crew schedules...")
        
        input_data = state.input_data
        risk = state.risk_assessment
        
        flight_count = len(input_data.get("flights", []))
        delay_minutes = risk.get("duration_minutes", 120)
        
        # Use crew scheduling tool
        result = await crew_scheduling_tool(
            flight_count=flight_count,
            delay_minutes=delay_minutes,
            crew_available=10
        )
        
        state.crew_rotation = result
        state = log_reasoning(state, self.name, {"flights": flight_count}, result)
        
        logger.info(
            f"👔 Crew: Changes={'Required' if result['crew_changes_needed'] else 'Not needed'}, "
            f"Backup={result['backup_crew_required']}"
        )
        
        return state


class AggregatorAgent:
    """Aggregator agent for synthesizing all outputs."""
    
    def __init__(self):
        self.name = "AggregatorAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Aggregate all agent outputs into final plan.
        
        Args:
            state: Current disruption state with all agent outputs
            
        Returns:
            Updated state with final plan
        """
        logger.info("📋 AGGREGATOR AGENT (ADK): Synthesizing final plan...")
        
        final_plan = {
            "disruption_detected": state.disruption_detected,
            "risk_assessment": state.risk_assessment,
            "signal_breakdown": state.signal_breakdown,
            "rebooking_plan": state.rebooking_plan,
            "finance_estimate": state.finance_estimate,
            "crew_rotation": state.crew_rotation,
            "what_if_scenarios": state.simulation_results,
            "recommended_action": "PROCEED" if state.disruption_detected else "MONITOR",
            "confidence": "high" if len(state.audit_log) > 5 else "medium",
            "generated_at": state.audit_log[-1]["timestamp"] if state.audit_log else None,
        }
        
        # Calculate priority
        risk_likelihood = state.risk_assessment.get("likelihood", 0)
        if risk_likelihood > 0.8:
            final_plan["priority"] = "critical"
        elif risk_likelihood > 0.6:
            final_plan["priority"] = "high"
        else:
            final_plan["priority"] = "medium"
        
        state.final_plan = final_plan
        state = log_reasoning(state, self.name, state.simulation_results, final_plan)
        
        logger.info(
            f"✅ Final Plan: Priority={final_plan['priority']}, "
            f"Action={final_plan['recommended_action']}"
        )
        
        return state
