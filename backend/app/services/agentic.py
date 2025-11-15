"""Service layer for APIV2 (ADK) workflow orchestration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Literal

import httpx

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
        self._remote_enabled = bool(settings.agentic_apiv2_base_url)

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
        
        if self._should_proxy_to_remote(engine_name):
            logger.info("🌐 AgenticService: Proxying to google_a2a_agents_apiV2 endpoint")
            result = await self._run_remote_workflow(flight_data)
        else:
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

    def _should_proxy_to_remote(self, engine: EngineName) -> bool:
        return engine == "apiv2" and self._remote_enabled

    def _build_remote_url(self) -> str:
        base = settings.agentic_apiv2_base_url
        if not base:
            raise ValueError("AGENTIC_APIV2_BASE_URL is not configured")
        path = settings.agentic_apiv2_analyze_path or "/api/v2/agents/analyze"
        return f"{base}{path}"

    def _prepare_remote_payload(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(flight_data)
        timestamp = (
            flight_data.get("timestamp")
            or flight_data.get("generatedAt")
            or datetime.utcnow().isoformat() + "Z"
        )
        payload["timestamp"] = timestamp
        payload.setdefault("airport", flight_data.get("airport"))
        payload.setdefault("carrier", flight_data.get("carrier"))
        payload.setdefault("stats", flight_data.get("stats", {}))
        payload.setdefault("flights", flight_data.get("flights", []))
        payload.setdefault("alerts", flight_data.get("alerts", []))
        return payload

    def _transform_remote_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "final_plan": data.get("final_plan", {}),
            "audit_log": data.get("audit_log", []),
            "disruption_detected": data.get("disruption_detected", False),
            "risk_assessment": data.get("risk_assessment", {}),
            "rebooking_plan": data.get("rebooking_plan", {}),
            "finance_estimate": data.get("finance_estimate", {}),
            "crew_rotation": data.get("crew_rotation", {}),
            "simulation_results": data.get("simulation_results", []),
            "decision_log": data.get("decision_log", []),
        }
        # Preserve any additional metadata for downstream consumers
        for key in ("metadata", "trace_id", "engine"):
            if key in data:
                result[key] = data[key]
        return result

    async def _run_remote_workflow(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        url = self._build_remote_url()
        payload = self._prepare_remote_payload(flight_data)
        headers = {"Content-Type": "application/json"}
        if settings.agentic_apiv2_api_key:
            headers["Authorization"] = f"Bearer {settings.agentic_apiv2_api_key}"
        timeout = settings.agentic_apiv2_timeout or 30.0
        logger.info("🌍 Posting payload to %s (timeout %.1fs)", url, timeout)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.RequestError as exc:  # pragma: no cover - network edge
            raise RuntimeError(
                f"Failed to reach google_a2a_agents_apiV2 endpoint: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise RuntimeError(
                f"google_a2a_agents_apiV2 returned HTTP {response.status_code}: {response.text}"
            )

        data: Dict[str, Any]
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("Remote APIV2 response was not valid JSON") from exc

        if not data.get("success", True):
            message = data.get("error") or data.get("detail") or "Unknown remote error"
            raise RuntimeError(f"google_a2a_agents_apiV2 error: {message}")

        return self._transform_remote_response(data)

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
                "decision_log": result.get("decision_log", []),
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
                "decision_log": result.get("decision_log", []),
            }
            await sim_collection.insert_one(sim_doc)


agentic_service = AgenticService()
