import pytest

from app.agentsv2 import tools
from app.agentsv2.tools import (
    predictive_signal_tool,
    rebooking_tool,
    finance_tool,
    crew_scheduling_tool,
)


@pytest.mark.asyncio
async def test_predictive_signal_tool_returns_risk_fields() -> None:
    result = await predictive_signal_tool(
        airport="HKG",
        carrier="CX",
        weather_score=0.8,
        aircraft_score=0.3,
        crew_score=0.4,
    )

    assert "risk_probability" in result
    assert "disruption_detected" in result
    assert 0.0 <= result["risk_probability"] <= 1.0


@pytest.mark.asyncio
async def test_rebooking_tool_synthetic_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force synthetic mode regardless of Amadeus availability
    monkeypatch.setattr(tools, "AMADEUS_AVAILABLE", False, raising=False)

    result = await rebooking_tool(
        flight_id="CX888",
        pax_count=120,
        delay_minutes=45,
        vip_count=10,
    )

    assert result["data_source"] == "synthetic"
    assert result["flight_id"] == "CX888"
    assert result["estimated_pax"] == 120
    assert result["vip_count"] == 10
    assert isinstance(result["actions"], list) and result["actions"]


@pytest.mark.asyncio
async def test_rebooking_tool_uses_amadeus_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    # Pretend Amadeus tooling and credentials are available
    monkeypatch.setattr(tools, "AMADEUS_AVAILABLE", True, raising=False)
    monkeypatch.setattr(tools.settings, "amadeus_client_id", "dummy", raising=False)
    monkeypatch.setattr(tools.settings, "amadeus_client_secret", "dummy", raising=False)

    async def fake_comprehensive_reaccommodation_tool(
        origin: str,
        destination: str,
        original_departure_date: str,
        passenger_count: int,
        vip_count: int = 0,
        delay_minutes: int = 0,
    ) -> dict:
        return {
            "flight_options": {"alternatives": [], "count": 0},
            "hotel_options": None,
            "recommended_plan": {
                "strategy": "next_day_with_hotel",
                "priority": "high",
                "actions": [
                    {"type": "rebook_flight", "details": "Rebook on CX888"},
                    {"type": "notify_passengers", "details": "Notify pax"},
                ],
            },
            "total_cost_estimate": 123456.0,
            "needs_hotel": True,
            "reasoning": "stubbed for test",
        }

    monkeypatch.setattr(
        tools,
        "comprehensive_reaccommodation_tool",
        fake_comprehensive_reaccommodation_tool,
        raising=True,
    )

    result = await rebooking_tool(
        flight_id="CX888",
        pax_count=150,
        delay_minutes=240,
        vip_count=15,
        origin="HKG",
        destination="LAX",
        departure_date="2025-12-01",
    )

    assert result["data_source"] == "amadeus"
    assert result["strategy"] == "next_day_with_hotel"
    assert result["hotel_required"] is True
    assert result["estimated_pax"] == 150
    assert result["vip_count"] == 15
    assert result["total_cost_estimate"] == 123456.0


@pytest.mark.asyncio
async def test_finance_tool_produces_consistent_totals() -> None:
    result = await finance_tool(
        pax_count=100,
        delay_minutes=200,
        hotel_required=True,
        flight_distance="medium",
    )

    assert result["total_usd"] >= 0
    assert result["total_usd"] == (
        result["compensation_usd"]
        + result["hotel_meals_usd"]
        + result["operational_usd"]
    )
    assert isinstance(result["breakdown"], list) and result["breakdown"]


@pytest.mark.asyncio
async def test_crew_scheduling_tool_flags_changes_for_long_delays() -> None:
    result = await crew_scheduling_tool(
        flight_count=3,
        delay_minutes=200,
        crew_available=5,
    )

    assert result["crew_changes_needed"] is True
    assert 0 < result["backup_crew_required"] <= 5
    assert isinstance(result["regulatory_issues"], list)
    assert isinstance(result["actions"], list) and result["actions"]
