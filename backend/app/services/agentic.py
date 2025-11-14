"""Service layer for APIV2 (ADK) workflow orchestration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Literal

from ..agentsv2 import APIV2Workflow
from ..config import AGENTIC_ENGINES, settings
from .mongo_client import get_client

logger = logging.getLogger(__name__)

EngineName = Literal["apiv2"]


class AgenticService:
    """Orchestrates disruption analyses across multiple agent engines."""

    def __init__(self) -> None:
        self._mongo_client = None
        self._workflow_cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def analyze_disruption(
        self,
        flight_data: Dict[str, Any],
        *,
        engine: str | None = None,
    ) -> Dict[str, Any]:
        if not settings.agentic_enabled:
            raise ValueError("Agentic mode is not enabled. Set AGENTIC_ENABLED=true")

        engine_name = self._normalize_engine(engine)
        logger.info(f"🔧 AgenticService: Using engine '{engine_name}'")
        logger.info(f"   Flight: {flight_data.get('flight_number', 'N/A')}")
        logger.info(f"   Stats: {flight_data.get('stats', {})}")
        
        workflow = self._get_workflow(engine_name)
        logger.info(f"🏃 AgenticService: Running {engine_name} workflow...")

        result = await workflow.run(flight_data)
        result.setdefault("engine", engine_name)
        
        logger.info(f"✅ AgenticService: Workflow complete, persisting results...")
        await self._persist_analysis(result, flight_data, engine_name)
        
        return result

    async def get_recent_analyses(
        self,
        airport: str,
        carrier: str,
        limit: int = 10,
        *,
        engine: str | None = None,
    ) -> list[Dict[str, Any]]:
        query: Dict[str, Any] = {"airport": airport, "carrier": carrier}
        normalized = self._maybe_normalize_engine(engine)
        if normalized:
            query["engine"] = normalized

        db = self.mongo_client[settings.mongo_db_name]
        audit_collection = db[settings.mongo_agent_audit_collection]

        cursor = audit_collection.find(query).sort("timestamp", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def get_simulation_history(
        self,
        airport: str,
        carrier: str,
        limit: int = 10,
        *,
        engine: str | None = None,
    ) -> list[Dict[str, Any]]:
        query: Dict[str, Any] = {"airport": airport, "carrier": carrier}
        normalized = self._maybe_normalize_engine(engine)
        if normalized:
            query["engine"] = normalized

        db = self.mongo_client[settings.mongo_db_name]
        sim_collection = db[settings.mongo_simulation_collection]

        cursor = sim_collection.find(query).sort("timestamp", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @property
    def mongo_client(self):
        if self._mongo_client is None:
            self._mongo_client = get_client()
        return self._mongo_client

    def _normalize_engine(self, engine: str | None) -> EngineName:
        requested = (engine or settings.agentic_mode or "apiv2").lower()
        if requested not in AGENTIC_ENGINES:
            raise ValueError(
                f"Unsupported agentic engine '{engine}'. Choose from {sorted(AGENTIC_ENGINES)}."
            )
        return requested  # type: ignore[return-value]

    def _maybe_normalize_engine(self, engine: str | None) -> EngineName | None:
        if not engine:
            return None
        return self._normalize_engine(engine)

    def _get_workflow(self, engine: EngineName):
        if engine in self._workflow_cache:
            return self._workflow_cache[engine]

        # Only APIV2/ADK workflow is supported
        workflow = APIV2Workflow()
        logger.info(f"🔧 Initialized APIV2 (ADK) workflow instance")

        self._workflow_cache[engine] = workflow
        return workflow

    async def _persist_analysis(
        self,
        result: Dict[str, Any],
        flight_data: Dict[str, Any],
        engine: EngineName,
    ) -> None:
        db = self.mongo_client[settings.mongo_db_name]

        if result.get("audit_log"):
            audit_collection = db[settings.mongo_agent_audit_collection]
            audit_doc = {
                "timestamp": datetime.utcnow(),
                "airport": flight_data.get("airport"),
                "carrier": flight_data.get("carrier"),
                "engine": engine,
                "disruption_detected": result.get("disruption_detected"),
                "audit_log": result["audit_log"],
                "final_plan": result.get("final_plan", {}),
            }
            await audit_collection.insert_one(audit_doc)

        if result.get("simulation_results"):
            sim_collection = db[settings.mongo_simulation_collection]
            sim_doc = {
                "timestamp": datetime.utcnow(),
                "airport": flight_data.get("airport"),
                "carrier": flight_data.get("carrier"),
                "engine": engine,
                "scenarios": result["simulation_results"],
                "risk_assessment": result.get("risk_assessment", {}),
                "final_plan": result.get("final_plan", {}),
            }
            await sim_collection.insert_one(sim_doc)


agentic_service = AgenticService()
