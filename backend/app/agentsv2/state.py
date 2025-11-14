"""State management for ADK-based disruption workflow.

ADK uses message-passing and shared context, similar to LangGraph's AgentState.
This module defines the state structure and logging utilities.
"""

from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class DisruptionState(BaseModel):
    """Shared state for the ADK-based disruption workflow.
    
    This state is passed between agents and accumulates results.
    Uses Pydantic for validation and serialization.
    """
    
    # Input data from provider
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flight details and signals from monitor"
    )
    
    # Detection & assessment
    disruption_detected: bool = Field(
        default=False,
        description="Whether a disruption was detected"
    )
    risk_assessment: Dict[str, Any] = Field(
        default_factory=dict,
        description="Risk assessment from predictive analysis"
    )
    signal_breakdown: Dict[str, Any] = Field(
        default_factory=dict,
        description="Breakdown of risk signals (weather, aircraft, crew)"
    )
    
    # Agent outputs
    rebooking_plan: Dict[str, Any] = Field(
        default_factory=dict,
        description="Passenger re-accommodation plan"
    )
    finance_estimate: Dict[str, Any] = Field(
        default_factory=dict,
        description="Financial impact estimate"
    )
    crew_rotation: Dict[str, Any] = Field(
        default_factory=dict,
        description="Crew scheduling adjustments"
    )
    
    # What-if simulations
    simulation_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from what-if scenario simulations"
    )
    
    # Transparency & audit
    audit_log: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Immutable append-only log of all agent reasoning"
    )
    
    # Final aggregated output
    final_plan: Dict[str, Any] = Field(
        default_factory=dict,
        description="Final aggregated action plan"
    )
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


def log_reasoning(
    state: DisruptionState,
    agent_name: str,
    input_data: Any,
    output: Any
) -> DisruptionState:
    """Append transparent reasoning trace to audit log.
    
    Args:
        state: Current disruption state
        agent_name: Name of the agent logging the trace
        input_data: Input received by the agent
        output: Output produced by the agent
        
    Returns:
        Updated state with new audit log entry
    """
    trace = {
        "agent": agent_name,
        "input": input_data,
        "output": output,
        "timestamp": datetime.now().isoformat(),
    }
    state.audit_log.append(trace)
    return state


def create_initial_state(flight_data: Dict[str, Any]) -> DisruptionState:
    """Create initial state from flight monitor data.
    
    Args:
        flight_data: Output from FlightMonitorProvider
        
    Returns:
        Initialized DisruptionState
    """
    return DisruptionState(input_data=flight_data)
