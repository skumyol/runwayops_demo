"""LangGraph workflow definition for multi-agent disruption management.

This module builds the stateful graph that orchestrates all agents.
"""

from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from .nodes import (
    aggregator_node,
    crew_node,
    finance_node,
    orchestrator_node,
    predictive_node,
    rebooking_node,
    risk_node,
    route_after_predictive,
)
from .state import AgentState


class DisruptionWorkflow:
    """LangGraph-based workflow for flight disruption management.
    
    This workflow:
    1. Detects disruptions using predictive signals
    2. Routes to orchestrator if disruption detected
    3. Runs specialized agents in parallel (risk, rebooking, finance, crew)
    4. Aggregates results into a final action plan
    5. Logs all reasoning for transparency and audit
    
    Usage:
        workflow = DisruptionWorkflow()
        result = await workflow.run(flight_monitor_data)
    """
    
    def __init__(self):
        """Initialize the workflow graph."""
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph state graph with all nodes and edges."""
        
        # Initialize graph with AgentState
        graph = StateGraph(AgentState)
        
        # Add all nodes
        graph.add_node("predictive", predictive_node)
        graph.add_node("orchestrator", orchestrator_node)
        graph.add_node("risk", risk_node)
        graph.add_node("rebooking", rebooking_node)
        graph.add_node("finance", finance_node)
        graph.add_node("crew", crew_node)
        graph.add_node("aggregator", aggregator_node)
        
        # Set entry point
        graph.set_entry_point("predictive")
        
        # Conditional routing after predictive
        graph.add_conditional_edges(
            "predictive",
            route_after_predictive,
            {
                "orchestrator": "orchestrator",
                "end": END,
            }
        )
        
        # After orchestrator, fan out to parallel sub-agents
        graph.add_edge("orchestrator", "risk")
        graph.add_edge("orchestrator", "rebooking")
        graph.add_edge("orchestrator", "finance")
        graph.add_edge("orchestrator", "crew")
        
        # All sub-agents converge to aggregator
        graph.add_edge("risk", "aggregator")
        graph.add_edge("rebooking", "aggregator")
        graph.add_edge("finance", "aggregator")
        graph.add_edge("crew", "aggregator")
        
        # Aggregator is the final node
        graph.add_edge("aggregator", END)
        
        # Compile the graph
        return graph.compile()
    
    async def run(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with flight monitor data.
        
        Args:
            flight_data: Output from a FlightMonitorProvider (stats, flights, alerts)
            
        Returns:
            Dictionary containing:
                - final_plan: Aggregated action plan
                - audit_log: Complete reasoning trace from all agents
                - disruption_detected: Boolean flag
        """
        
        # Initialize state
        initial_state: AgentState = {
            "input_data": flight_data,
            "disruption_detected": False,
            "risk_assessment": {},
            "rebooking_plan": {},
            "finance_estimate": {},
            "crew_rotation": {},
            "simulation_results": [],
            "audit_log": [],
            "final_plan": {},
        }
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state)
        
        return {
            "final_plan": result.get("final_plan", {}),
            "audit_log": result.get("audit_log", []),
            "disruption_detected": result.get("disruption_detected", False),
            "risk_assessment": result.get("risk_assessment", {}),
            "rebooking_plan": result.get("rebooking_plan", {}),
            "finance_estimate": result.get("finance_estimate", {}),
            "crew_rotation": result.get("crew_rotation", {}),
            "simulation_results": result.get("simulation_results", []),
        }
    
    def run_sync(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous version of run() for non-async contexts.
        
        Args:
            flight_data: Output from a FlightMonitorProvider
            
        Returns:
            Same as run()
        """
        initial_state: AgentState = {
            "input_data": flight_data,
            "disruption_detected": False,
            "risk_assessment": {},
            "rebooking_plan": {},
            "finance_estimate": {},
            "crew_rotation": {},
            "simulation_results": [],
            "audit_log": [],
            "final_plan": {},
        }
        
        result = self.graph.invoke(initial_state)
        
        return {
            "final_plan": result.get("final_plan", {}),
            "audit_log": result.get("audit_log", []),
            "disruption_detected": result.get("disruption_detected", False),
            "risk_assessment": result.get("risk_assessment", {}),
            "rebooking_plan": result.get("rebooking_plan", {}),
            "finance_estimate": result.get("finance_estimate", {}),
            "crew_rotation": result.get("crew_rotation", {}),
            "simulation_results": result.get("simulation_results", []),
        }
