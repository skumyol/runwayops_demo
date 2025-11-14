"""FastAPI integration for ADK-based disruption workflow.

This module provides REST API endpoints for the ADK workflow,
allowing integration with the existing FastAPI backend.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .workflow import DisruptionWorkflowADK


logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v2/agents", tags=["ADK Agents"])

# Initialize workflow singleton
_workflow_instance = None


def get_workflow() -> DisruptionWorkflowADK:
    """Get or create workflow singleton instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = DisruptionWorkflowADK()
        logger.info("✅ ADK Workflow initialized")
    return _workflow_instance


# Request/Response Models
class FlightData(BaseModel):
    """Flight monitor data input."""
    airport: str = Field(..., description="Airport code (e.g., HKG)")
    carrier: str = Field(..., description="Carrier code (e.g., CX)")
    timestamp: str = Field(..., description="Timestamp of data")
    stats: Dict[str, Any] = Field(..., description="Flight statistics")
    flights: list = Field(default_factory=list, description="Flight records")
    alerts: list = Field(default_factory=list, description="Active alerts")


class DisruptionResponse(BaseModel):
    """Disruption workflow response."""
    success: bool = Field(..., description="Whether execution succeeded")
    disruption_detected: bool = Field(..., description="Whether disruption detected")
    final_plan: Dict[str, Any] = Field(..., description="Final action plan")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    rebooking_plan: Dict[str, Any] = Field(default_factory=dict)
    finance_estimate: Dict[str, Any] = Field(default_factory=dict)
    crew_rotation: Dict[str, Any] = Field(default_factory=dict)
    simulation_results: list = Field(default_factory=list)
    audit_log: list = Field(default_factory=list)
    error: str = Field(None, description="Error message if failed")


@router.post("/analyze", response_model=DisruptionResponse)
async def analyze_disruption(flight_data: FlightData) -> DisruptionResponse:
    """Analyze flight data for potential disruptions using ADK workflow.
    
    This endpoint accepts flight monitor data and runs the multi-agent
    disruption analysis workflow.
    
    Args:
        flight_data: Flight statistics, records, and alerts
        
    Returns:
        DisruptionResponse with analysis results
        
    Raises:
        HTTPException: If workflow execution fails
    """
    try:
        logger.info(f"🔍 Analyzing disruption for {flight_data.airport}/{flight_data.carrier}")
        
        # Get workflow instance
        workflow = get_workflow()
        
        # Execute workflow
        result = await workflow.run(flight_data.dict())
        
        # Format response
        response = DisruptionResponse(
            success=True,
            disruption_detected=result.get("disruption_detected", False),
            final_plan=result.get("final_plan", {}),
            risk_assessment=result.get("risk_assessment", {}),
            rebooking_plan=result.get("rebooking_plan", {}),
            finance_estimate=result.get("finance_estimate", {}),
            crew_rotation=result.get("crew_rotation", {}),
            simulation_results=result.get("simulation_results", []),
            audit_log=result.get("audit_log", [])
        )
        
        logger.info(
            f"✅ Analysis complete: Disruption={response.disruption_detected}, "
            f"Priority={response.final_plan.get('priority', 'N/A')}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Disruption analysis failed: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for ADK workflow.
    
    Returns:
        Health status
    """
    try:
        workflow = get_workflow()
        return {
            "status": "healthy",
            "service": "ADK Disruption Workflow",
            "workflow": workflow.__class__.__name__
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/info")
async def workflow_info() -> Dict[str, Any]:
    """Get information about the ADK workflow.
    
    Returns:
        Workflow configuration and agent information
    """
    workflow = get_workflow()
    
    return {
        "workflow": "DisruptionWorkflowADK",
        "framework": "Google Agent Development Kit (ADK)",
        "agents": [
            "PredictiveAgent",
            "OrchestratorAgent",
            "RiskAgent",
            "RebookingAgent",
            "FinanceAgent",
            "CrewAgent",
            "AggregatorAgent"
        ],
        "tools": [
            "predictive_signal_tool",
            "rebooking_tool",
            "finance_tool",
            "crew_scheduling_tool"
        ],
        "features": [
            "Predictive disruption detection",
            "Multi-agent orchestration",
            "What-if scenario simulation",
            "Parallel agent execution",
            "Comprehensive audit logging",
            "VIP passenger prioritization",
            "EU261/HKCAD compliance"
        ]
    }
