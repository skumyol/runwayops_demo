import pytest

from app.agentsv2 import agents
from app.agentsv2.agents import (
    PredictiveAgent,
    OrchestratorAgent,
    RiskAgent,
    RebookingAgent,
    FinanceAgent,
    CrewAgent,
    AggregatorAgent,
    LLMBackedAgent,
)
from app.agentsv2.state import DisruptionState


@pytest.mark.asyncio
async def test_predictive_agent_updates_state_and_audit_log(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_predictive_signal_tool(**_: object) -> dict:
        return {
            "disruption_detected": True,
            "risk_probability": 0.9,
            "signal_breakdown": {"weather": {"score": 0.9}},
        }

    monkeypatch.setattr(agents, "predictive_signal_tool", fake_predictive_signal_tool)

    state = DisruptionState(
        input_data={
            "airport": "HKG",
            "carrier": "CX",
            "stats": {
                "weatherScore": 0.8,
                "aircraftScore": 0.6,
                "crewScore": 0.5,
            },
        }
    )

    agent = PredictiveAgent()
    new_state = await agent.run(state)

    assert new_state.disruption_detected is True
    assert new_state.risk_assessment["risk_probability"] == 0.9
    assert new_state.audit_log and new_state.audit_log[-1]["agent"] == "PredictiveAgent"


@pytest.mark.asyncio
async def test_predictive_agent_uses_confirmed_disruption_ground_truth() -> None:
    state = DisruptionState(
        input_data={
            "airport": "HKG",
            "carrier": "CX",
            "stats": {
                "weatherScore": 0.1,
                "aircraftScore": 0.1,
                "crewScore": 0.1,
            },
            # Confirmed disruption from Mongo-backed flows
            "disruption": {
                "type": "cancellation",
                "rootCause": "Weather en-route",
            },
        }
    )

    agent = PredictiveAgent()
    new_state = await agent.run(state)

    # Ground truth should override heuristic and force disruption_detected
    assert new_state.disruption_detected is True
    assert new_state.risk_assessment["risk_probability"] == 1.0
    assert "Confirmed disruption" in new_state.risk_assessment["reasoning"]
    assert new_state.audit_log and new_state.audit_log[-1]["agent"] == "PredictiveAgent"


@pytest.mark.asyncio
async def test_orchestrator_agent_uses_heuristic_fallback_without_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_llm_json(self: LLMBackedAgent, prompt: str) -> None:  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(LLMBackedAgent, "_invoke_llm_json", fake_llm_json)

    state = DisruptionState(
        input_data={"airport": "HKG", "carrier": "CX", "stats": {}},
        disruption_detected=True,
        risk_assessment={"risk_probability": 0.85},
    )

    agent = OrchestratorAgent()
    new_state = await agent.run(state)

    assert new_state.simulation_results
    scenarios = {s["scenario"] for s in new_state.simulation_results}
    assert {"delay_3hr", "crew_unavailable"}.issubset(scenarios)
    assert new_state.audit_log and new_state.audit_log[-1]["agent"] == "OrchestratorAgent"


@pytest.mark.asyncio
async def test_risk_agent_enhances_risk_assessment_without_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_llm_json(self: LLMBackedAgent, prompt: str) -> None:  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(LLMBackedAgent, "_invoke_llm_json", fake_llm_json)

    state = DisruptionState(
        input_data={},
        risk_assessment={"risk_probability": 0.7},
    )

    agent = RiskAgent()
    new_state = await agent.run(state)

    ra = new_state.risk_assessment
    assert 0.0 <= ra["likelihood"] <= 1.0
    assert isinstance(ra["duration_minutes"], int)
    assert ra["pax_impact"] in {"low", "medium", "high"}
    assert "regulatory_risk" in ra


@pytest.mark.asyncio
async def test_rebooking_agent_applies_tool_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_rebooking_tool(**_: object) -> dict:
        return {
            "flight_id": "CX888",
            "strategy": "same_day_alternate",
            "hotel_required": False,
            "vip_priority": True,
            "estimated_pax": 150,
            "vip_count": 15,
            "delay_minutes": 90,
            "actions": ["reprotect pax"],
            "data_source": "synthetic",
        }

    async def fake_llm_json(self: LLMBackedAgent, prompt: str) -> None:  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(agents, "rebooking_tool", fake_rebooking_tool)
    monkeypatch.setattr(LLMBackedAgent, "_invoke_llm_json", fake_llm_json)

    state = DisruptionState(
        input_data={
            "airport": "HKG",
            "carrier": "CX",
            "stats": {"paxImpacted": 150},
            "flights": [
                {
                    "id": "CX888",
                    "flightNumber": "CX888",
                    "route": "HKG - LAX",
                    "destination": "LAX",
                    "statusCategory": "critical",
                    "scheduledDeparture": "2025-12-01T10:00:00Z",
                }
            ],
        },
        risk_assessment={"duration_minutes": 120},
    )

    agent = RebookingAgent()
    new_state = await agent.run(state)

    plan = new_state.rebooking_plan
    assert plan["flight_id"] == "CX888"
    assert plan["strategy"] == "same_day_alternate"
    assert plan["estimated_pax"] == 150
    assert new_state.audit_log and new_state.audit_log[-1]["agent"] == "RebookingAgent"


@pytest.mark.asyncio
async def test_finance_agent_merges_tool_result(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_finance_tool(**_: object) -> dict:
        return {
            "compensation_usd": 1000,
            "hotel_meals_usd": 500,
            "operational_usd": 200,
            "total_usd": 1700,
            "breakdown": ["stub"],
            "reasoning": "stub",
        }

    async def fake_llm_json(self: LLMBackedAgent, prompt: str) -> None:  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(agents, "finance_tool", fake_finance_tool)
    monkeypatch.setattr(LLMBackedAgent, "_invoke_llm_json", fake_llm_json)

    state = DisruptionState(
        input_data={},
        rebooking_plan={"estimated_pax": 50, "hotel_required": True},
        risk_assessment={"duration_minutes": 180},
    )

    agent = FinanceAgent()
    new_state = await agent.run(state)

    est = new_state.finance_estimate
    assert est["total_usd"] == 1700
    assert new_state.audit_log and new_state.audit_log[-1]["agent"] == "FinanceAgent"


@pytest.mark.asyncio
async def test_crew_agent_uses_tool_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_crew_tool(**_: object) -> dict:
        return {
            "crew_changes_needed": True,
            "backup_crew_required": 2,
            "crew_available": 10,
            "regulatory_issues": ["duty limit"],
            "actions": ["assign backup"],
            "reasoning": "stub",
        }

    async def fake_llm_json(self: LLMBackedAgent, prompt: str) -> None:  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(agents, "crew_scheduling_tool", fake_crew_tool)
    monkeypatch.setattr(LLMBackedAgent, "_invoke_llm_json", fake_llm_json)

    state = DisruptionState(
        input_data={"flights": [{"id": "CX888"}]},
        risk_assessment={"duration_minutes": 200},
    )

    agent = CrewAgent()
    new_state = await agent.run(state)

    crew = new_state.crew_rotation
    assert crew["crew_changes_needed"] is True
    assert crew["backup_crew_required"] == 2
    assert new_state.audit_log and new_state.audit_log[-1]["agent"] == "CrewAgent"


@pytest.mark.asyncio
async def test_aggregator_agent_builds_final_plan() -> None:
    state = DisruptionState(
        input_data={},
        disruption_detected=True,
        risk_assessment={"risk_probability": 0.8, "likelihood": 0.8},
        signal_breakdown={"weather": {"score": 0.9}},
        rebooking_plan={"strategy": "next_day", "hotel_required": True},
        finance_estimate={"total_usd": 100000},
        crew_rotation={"crew_changes_needed": True},
        simulation_results=[{"scenario": "delay_3hr"}],
        audit_log=[],
    )

    agent = AggregatorAgent()
    new_state = await agent.run(state)

    plan = new_state.final_plan
    assert plan["disruption_detected"] is True
    assert plan["recommended_action"] in {"PROCEED", "MONITOR"}
    assert plan["priority"] in {"high", "critical", "medium"}
    assert new_state.audit_log and new_state.audit_log[-1]["agent"] == "AggregatorAgent"
