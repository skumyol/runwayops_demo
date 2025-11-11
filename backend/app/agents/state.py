"""State definitions for the LangGraph disruption workflow."""

from datetime import datetime
from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict):
    """Shared state across all agents in the disruption workflow.
    
    This state is passed between nodes and accumulates results from each agent.
    All reasoning traces are appended to audit_log for transparency.
    """
    
    # Input data from provider
    input_data: Dict[str, Any]  # Flight details + signals from monitor
    
    # Detection & assessment
    disruption_detected: bool
    risk_assessment: Dict[str, Any]
    
    # Agent outputs
    rebooking_plan: Dict[str, Any]
    finance_estimate: Dict[str, Any]
    crew_rotation: Dict[str, Any]
    
    # What-if simulations
    simulation_results: List[Dict[str, Any]]
    
    # Transparency & audit
    audit_log: List[Dict[str, Any]]  # Immutable append-only log
    
    # Final aggregated output
    final_plan: Dict[str, Any]


def log_reasoning(
    state: AgentState, agent_name: str, input_data: Any, output: Any
) -> AgentState:
    """Helper to append transparent reasoning trace to audit log.
    
    Args:
        state: Current agent state
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
    state["audit_log"].append(trace)
    return state
