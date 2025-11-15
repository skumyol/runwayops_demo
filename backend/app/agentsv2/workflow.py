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
from .state import DisruptionState, create_initial_state, record_progress


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
            state = record_progress(state, "Workflow", "started", "Starting disruption analysis...")
            state = record_progress(state, "PredictiveAgent", "started", "Analyzing disruption signals...")
            state = await self.predictive_agent.run(state)
            state = record_progress(state, "PredictiveAgent", "complete", "Disruption analysis complete")
            
            # Conditional routing: Only proceed if disruption detected
            if not state.disruption_detected:
                logger.info("✓ No disruption detected - workflow complete")
                state = record_progress(state, "Workflow", "complete", "No disruption detected - monitoring only")
                state.final_plan = {
                    "disruption_detected": False,
                    "recommended_action": "MONITOR",
                    "priority": "low",
                    "message": "No action required"
                }
                return self._format_output(state)
            
            # Step 2: Orchestrator Agent
            logger.info("⚠️  Disruption detected - proceeding with orchestration")
            state = record_progress(state, "OrchestratorAgent", "started", "Coordinating response strategy...")
            state = await self.orchestrator_agent.run(state)
            state = record_progress(state, "OrchestratorAgent", "complete", "Response plan created")
            
            # Step 3: Sub-Agents with dependency order
            # Finance agent depends on Risk + Rebooking, so run in two phases
            import asyncio
            
            logger.info("🔄 Phase 1: Running Risk and Rebooking agents...")
            state = record_progress(state, "SubAgents", "started", "Running impact assessment agents...")
            
            # Phase 1: Risk and Rebooking can run in parallel
            state = record_progress(state, "RiskAgent", "started", "Assessing risk and impact...")
            state = record_progress(state, "RebookingAgent", "started", "Planning passenger re-accommodation...")
            
            risk_state, rebooking_state = await asyncio.gather(
                self.risk_agent.run(state),
                self.rebooking_agent.run(state)
            )
            
            # Both agents modify the same state object, use either result
            state = risk_state
            state = record_progress(state, "RiskAgent", "complete", "Risk assessment complete")
            state = record_progress(state, "RebookingAgent", "complete", "Rebooking plan ready")
            logger.info("✅ Phase 1 complete: Risk and Rebooking")
            
            # Phase 2: Finance and Crew can now run in parallel (Finance has its dependencies)
            logger.info("🔄 Phase 2: Running Finance and Crew agents...")
            state = record_progress(state, "FinanceAgent", "started", "Calculating financial impact...")
            state = record_progress(state, "CrewAgent", "started", "Managing crew schedules...")
            
            finance_state, crew_state = await asyncio.gather(
                self.finance_agent.run(state),
                self.crew_agent.run(state)
            )
            
            # Both agents modify the same state object, use either result
            state = finance_state
            state = record_progress(state, "FinanceAgent", "complete", "Cost estimate complete")
            state = record_progress(state, "CrewAgent", "complete", "Crew plan ready")
            logger.info("✅ Phase 2 complete: Finance and Crew")
            
            logger.info("✅ All sub-agents complete")
            
            # Step 4: Aggregator Agent
            state = record_progress(state, "AggregatorAgent", "started", "Synthesizing final plan...")
            state = await self.aggregator_agent.run(state)
            state = record_progress(state, "AggregatorAgent", "complete", "Final plan ready")
            state = record_progress(state, "Workflow", "complete", "Analysis complete")
            
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
            "decision_log": state.decision_log,
            "progress_updates": state.progress_updates,
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
