import pytest

from app.agentsv2 import agents
from app.agentsv2.workflow import DisruptionWorkflowADK
from app.agentsv2 import tools as tools_mod


@pytest.mark.asyncio
async def test_workflow_no_disruption_returns_monitor_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_predictive_signal_tool(**_: object) -> dict:
        return {
            "disruption_detected": False,
            "risk_probability": 0.1,
            "signal_breakdown": {},
        }

    async def fake_llm_json(self: agents.LLMBackedAgent, prompt: str) -> None:  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(agents, "predictive_signal_tool", fake_predictive_signal_tool)
    monkeypatch.setattr(agents.LLMBackedAgent, "_invoke_llm_json", fake_llm_json)
    monkeypatch.setattr(tools_mod, "AMADEUS_AVAILABLE", False, raising=False)

    workflow = DisruptionWorkflowADK()
    flight_data = {
        "airport": "HKG",
        "carrier": "CX",
        "stats": {},
        "flights": [],
        "alerts": [],
    }

    result = await workflow.run(flight_data)

    assert result["disruption_detected"] is False
    assert result["final_plan"]["recommended_action"] == "MONITOR"
    assert result["final_plan"]["priority"] == "low"


@pytest.mark.asyncio
async def test_workflow_runs_full_pipeline_on_disruption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_predictive_signal_tool(**_: object) -> dict:
        return {
            "disruption_detected": True,
            "risk_probability": 0.9,
            "signal_breakdown": {},
        }

    async def fake_llm_json(self: agents.LLMBackedAgent, prompt: str) -> None:  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(agents, "predictive_signal_tool", fake_predictive_signal_tool)
    monkeypatch.setattr(agents.LLMBackedAgent, "_invoke_llm_json", fake_llm_json)
    monkeypatch.setattr(tools_mod, "AMADEUS_AVAILABLE", False, raising=False)

    workflow = DisruptionWorkflowADK()
    flight_data = {
        "airport": "HKG",
        "carrier": "CX",
        "stats": {"paxImpacted": 200},
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
        "alerts": [],
    }

    result = await workflow.run(flight_data)

    assert result["disruption_detected"] is True
    assert result["final_plan"]["recommended_action"] in {"PROCEED", "MONITOR"}
    assert result["rebooking_plan"]
    assert result["finance_estimate"]
    assert result["crew_rotation"]
    assert result["audit_log"]
