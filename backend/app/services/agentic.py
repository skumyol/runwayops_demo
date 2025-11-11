"""Service layer for LangGraph agentic workflow integration.

This module provides the interface between FastAPI endpoints and the
LangGraph workflow, including MongoDB persistence for audit logs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from ..agents import DisruptionWorkflow
from ..config import settings
from .mongo_client import get_client


class AgenticService:
    """Service for managing agentic disruption analysis.
    
    Handles workflow execution and persistence of audit logs and simulations.
    """
    
    def __init__(self):
        """Initialize the service with workflow and MongoDB client."""
        self._workflow: DisruptionWorkflow | None = None
        self._mongo_client = None
    
    @property
    def workflow(self) -> DisruptionWorkflow:
        """Lazy-load the workflow to avoid initialization if agentic is disabled."""
        if self._workflow is None:
            self._workflow = DisruptionWorkflow()
        return self._workflow
    
    @property
    def mongo_client(self):
        """Get MongoDB client for persistence."""
        if self._mongo_client is None:
            self._mongo_client = get_client()
        return self._mongo_client
    
    async def analyze_disruption(
        self, flight_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the agentic workflow on flight monitor data.
        
        Args:
            flight_data: Output from FlightMonitorProvider (stats, flights, alerts)
            
        Returns:
            Dict containing final_plan, audit_log, and analysis results
            
        Raises:
            ValueError: If agentic mode is disabled or not configured
        """
        if not settings.agentic_enabled:
            raise ValueError("Agentic mode is not enabled. Set AGENTIC_ENABLED=true")
        
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be configured for agentic mode")
        
        # Execute workflow
        result = await self.workflow.run(flight_data)
        
        # Persist to MongoDB
        await self._persist_analysis(result, flight_data)
        
        return result
    
    async def _persist_analysis(
        self, result: Dict[str, Any], flight_data: Dict[str, Any]
    ) -> None:
        """Persist audit log and simulation results to MongoDB.
        
        Args:
            result: Output from workflow execution
            flight_data: Original input data
        """
        db = self.mongo_client[settings.mongo_db_name]
        
        # Persist audit log
        if result.get("audit_log"):
            audit_collection = db[settings.mongo_agent_audit_collection]
            audit_doc = {
                "timestamp": datetime.utcnow(),
                "airport": flight_data.get("airport"),
                "carrier": flight_data.get("carrier"),
                "disruption_detected": result.get("disruption_detected"),
                "audit_log": result["audit_log"],
                "final_plan": result.get("final_plan", {}),
            }
            await audit_collection.insert_one(audit_doc)
        
        # Persist simulation results
        if result.get("simulation_results"):
            sim_collection = db[settings.mongo_simulation_collection]
            sim_doc = {
                "timestamp": datetime.utcnow(),
                "airport": flight_data.get("airport"),
                "carrier": flight_data.get("carrier"),
                "scenarios": result["simulation_results"],
                "risk_assessment": result.get("risk_assessment", {}),
                "final_plan": result.get("final_plan", {}),
            }
            await sim_collection.insert_one(sim_doc)
    
    async def get_recent_analyses(
        self, airport: str, carrier: str, limit: int = 10
    ) -> list[Dict[str, Any]]:
        """Retrieve recent disruption analyses from MongoDB.
        
        Args:
            airport: Airport IATA code
            carrier: Carrier code
            limit: Maximum number of records to return
            
        Returns:
            List of recent analysis documents
        """
        db = self.mongo_client[settings.mongo_db_name]
        audit_collection = db[settings.mongo_agent_audit_collection]
        
        cursor = audit_collection.find(
            {"airport": airport, "carrier": carrier}
        ).sort("timestamp", -1).limit(limit)
        
        results = []
        async for doc in cursor:
            # Convert ObjectId to string for JSON serialization
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        return results
    
    async def get_simulation_history(
        self, airport: str, carrier: str, limit: int = 10
    ) -> list[Dict[str, Any]]:
        """Retrieve historical what-if simulations.
        
        Args:
            airport: Airport IATA code
            carrier: Carrier code
            limit: Maximum number of records to return
            
        Returns:
            List of simulation documents
        """
        db = self.mongo_client[settings.mongo_db_name]
        sim_collection = db[settings.mongo_simulation_collection]
        
        cursor = sim_collection.find(
            {"airport": airport, "carrier": carrier}
        ).sort("timestamp", -1).limit(limit)
        
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        return results


# Singleton instance
agentic_service = AgenticService()
