"""State management for ADK-based disruption workflow.

ADK uses message-passing and shared context, similar to LangGraph's AgentState.
This module defines the state structure and logging utilities.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
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
    what_if_templates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw scenario templates before enrichment"
    )
    
    # Transparency & audit
    audit_log: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Immutable append-only log of all agent reasoning"
    )
    decision_log: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Chronological decision trail from every agent"
    )
    
    # Final aggregated output
    final_plan: Dict[str, Any] = Field(
        default_factory=dict,
        description="Final aggregated action plan"
    )
    
    # Progress tracking for real-time updates
    progress_updates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Real-time progress updates for UI feedback"
    )
    
    # Progress callback (not serialized)
    _progress_callback: Optional[Callable[[str, str, str], None]] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True


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


def record_decision(
    state: DisruptionState,
    agent_name: str,
    decision: str,
    *,
    category: str | None = None,
    scenarios: List[str] | None = None,
    data: Dict[str, Any] | None = None,
) -> DisruptionState:
    """Record a structured decision for transparent what-if analysis."""
    entry = {
        "agent": agent_name,
        "decision": decision,
        "category": category or "general",
        "scenarios": scenarios or ["global"],
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    state.decision_log.append(entry)
    return state


def record_progress(
    state: DisruptionState,
    agent_name: str,
    status: str,
    message: str
) -> DisruptionState:
    """Record progress update for real-time UI feedback.
    
    Args:
        state: Current disruption state
        agent_name: Name of the agent reporting progress
        status: Status (started, running, complete, error)
        message: Human-readable progress message
        
    Returns:
        Updated state with progress entry
    """
    progress = {
        "agent": agent_name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    state.progress_updates.append(progress)
    
    # Call progress callback if set (for SSE streaming)
    if state._progress_callback:
        state._progress_callback(agent_name, status, message)
    
    return state


def create_initial_state(
    flight_data: Dict[str, Any],
    progress_callback: Optional[Callable[[str, str, str], None]] = None
) -> DisruptionState:
    """Create initial state from flight monitor data.
    
    Args:
        flight_data: Output from FlightMonitorProvider
        progress_callback: Optional callback for real-time progress updates
        
    Returns:
        Initialized DisruptionState
    """
    state = DisruptionState(input_data=flight_data)
    state._progress_callback = progress_callback
    return state
