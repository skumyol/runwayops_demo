"""ADK-based workflow orchestration for flight disruption management.

This module implements the multi-agent workflow using Google's Agent Development
Kit (ADK), mirroring the LangGraph implementation but with ADK's orchestration
primitives (Sequential, Parallel agents).
"""

import logging
from typing import Any, Dict

from .agents import (
    PredictiveAgent,
    OrchestratorAgent,
    RiskAgent,
    RebookingAgent,
    FinanceAgent,
    CrewAgent,
    AggregatorAgent,
)
from .state import DisruptionState, create_initial_state


logger = logging.getLogger(__name__)


class DisruptionWorkflowADK:
    """ADK-based workflow for flight disruption management.
    
    This workflow orchestrates multiple specialized agents:
    1. Predictive Agent - Detects disruptions from signals
    2. Orchestrator Agent - Creates action plans and what-if scenarios
    3. Parallel Sub-Agents:
        - Risk Agent - Assesses likelihood and impact
        - Rebooking Agent - Plans passenger re-accommodation
        - Finance Agent - Calculates financial impact
        - Crew Agent - Manages crew scheduling
    4. Aggregator Agent - Synthesizes final plan
    
    Architecture:
        Predictive → [If disruption] → Orchestrator → Parallel(Risk, Rebooking, Finance, Crew) → Aggregator
    
    Usage:
        workflow = DisruptionWorkflowADK()
        result = await workflow.run(flight_monitor_data)
    """
    
    def __init__(self):
        """Initialize the ADK workflow with all agents."""
        # Initialize all agents
        self.predictive_agent = PredictiveAgent()
        self.orchestrator_agent = OrchestratorAgent()
        self.risk_agent = RiskAgent()
        self.rebooking_agent = RebookingAgent()
        self.finance_agent = FinanceAgent()
        self.crew_agent = CrewAgent()
        self.aggregator_agent = AggregatorAgent()
        
        logger.info("✅ DisruptionWorkflowADK initialized with ADK agents")
        
        # In production ADK implementation, this would be:
        # from google.adk.agents import SequentialAgent, ParallelAgent
        #
        # self.workflow = SequentialAgent(
        #     name="disruption_workflow",
        #     description="Multi-agent flight disruption management",
        #     sub_agents=[
        #         self.predictive_agent,
        #         self.orchestrator_agent,
        #         ParallelAgent(
        #             name="sub_agents_parallel",
        #             sub_agents=[
        #                 self.risk_agent,
        #                 self.rebooking_agent,
        #                 self.finance_agent,
        #                 self.crew_agent
        #             ]
        #         ),
        #         self.aggregator_agent
        #     ]
        # )
    
    async def run(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the ADK workflow with flight monitor data.
        
        This method orchestrates all agents in sequence and parallel,
        implementing the disruption management workflow.
        
        Args:
            flight_data: Output from FlightMonitorProvider containing:
                - stats: Flight statistics and scores
                - flights: List of flight records
                - alerts: Active alerts
                
        Returns:
            Dictionary containing:
                - final_plan: Aggregated action plan
                - audit_log: Complete reasoning trace from all agents
                - disruption_detected: Boolean flag
                - risk_assessment: Risk analysis
                - rebooking_plan: Passenger re-accommodation plan
                - finance_estimate: Financial impact estimate
                - crew_rotation: Crew scheduling adjustments
                - simulation_results: What-if scenario results
        """
        logger.info("=" * 80)
        logger.info("🚀 Starting ADK Disruption Workflow")
        logger.info("=" * 80)
        
        # Initialize state
        state = create_initial_state(flight_data)
        
        try:
            # Step 1: Predictive Agent
            state = await self.predictive_agent.run(state)
            
            # Conditional routing: Only proceed if disruption detected
            if not state.disruption_detected:
                logger.info("✓ No disruption detected - workflow complete")
                state.final_plan = {
                    "disruption_detected": False,
                    "recommended_action": "MONITOR",
                    "priority": "low",
                    "message": "No action required"
                }
                return self._format_output(state)
            
            # Step 2: Orchestrator Agent
            logger.info("⚠️  Disruption detected - proceeding with orchestration")
            state = await self.orchestrator_agent.run(state)
            
            # Step 3: Parallel Sub-Agents
            # In production ADK, this would be handled by ParallelAgent
            # For now, we run sequentially (can be parallelized with asyncio.gather)
            logger.info("🔄 Running parallel sub-agents...")
            
            import asyncio
            
            # Run sub-agents in parallel
            risk_task = self.risk_agent.run(state)
            rebooking_task = self.rebooking_agent.run(state)
            finance_task = self.finance_agent.run(state)
            crew_task = self.crew_agent.run(state)
            
            # Wait for all to complete
            results = await asyncio.gather(
                risk_task,
                rebooking_task,
                finance_task,
                crew_task
            )
            
            # Merge results (all modify the same state object)
            # In ADK, this is handled automatically
            state = results[0]  # They all update the same state
            
            logger.info("✅ Parallel sub-agents complete")
            
            # Step 4: Aggregator Agent
            state = await self.aggregator_agent.run(state)
            
            logger.info("=" * 80)
            logger.info("✅ ADK Disruption Workflow Complete")
            logger.info("=" * 80)
            
            return self._format_output(state)
            
        except Exception as e:
            logger.error(f"❌ Workflow error: {e}", exc_info=True)
            # Return error state
            return {
                "error": str(e),
                "disruption_detected": state.disruption_detected,
                "audit_log": state.audit_log,
                "final_plan": {"error": "Workflow execution failed"}
            }
    
    def _format_output(self, state: DisruptionState) -> Dict[str, Any]:
        """Format state into output dictionary.
        
        Args:
            state: Final disruption state
            
        Returns:
            Formatted output dictionary
        """
        return {
            "final_plan": state.final_plan,
            "audit_log": state.audit_log,
            "disruption_detected": state.disruption_detected,
            "risk_assessment": state.risk_assessment,
            "signal_breakdown": state.signal_breakdown,
            "rebooking_plan": state.rebooking_plan,
            "finance_estimate": state.finance_estimate,
            "crew_rotation": state.crew_rotation,
            "simulation_results": state.simulation_results,
        }
    
    def run_sync(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for run() for non-async contexts.
        
        Args:
            flight_data: Output from FlightMonitorProvider
            
        Returns:
            Same as run()
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.run(flight_data))


# Convenience function for direct workflow execution
async def run_disruption_workflow(flight_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to run the disruption workflow.
    
    Args:
        flight_data: Flight monitor data
        
    Returns:
        Workflow execution results
    """
    workflow = DisruptionWorkflowADK()
    return await workflow.run(flight_data)
