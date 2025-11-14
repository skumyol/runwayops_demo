"""Helpers for injecting debug/what-if scenarios into flight data."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict


def _ensure_alerts(doc: Dict[str, Any]) -> None:
    if "alerts" not in doc or doc["alerts"] is None:
        doc["alerts"] = []


def _add_alert(doc: Dict[str, Any], message: str, level: str = "critical") -> None:
    _ensure_alerts(doc)
    doc["alerts"].append(
        {
            "level": level,
            "flightNumber": "MULTI",
            "message": message,
            "gate": "--",
            "delayMinutes": 180 if "3" in message else 60,
            "paxImpacted": 120,
            "recommendedAction": "Run AI analysis",
        }
    )


def apply_debug_scenario(flight_data: Dict[str, Any], scenario: str) -> Dict[str, Any]:
    """Return a copy of flight_data adjusted for the requested scenario."""

    scenario_key = (scenario or "").lower()
    if not scenario_key:
        return flight_data

    data = deepcopy(flight_data)
    stats = data.get("stats", {})
    flights = data.get("flights", [])
    crew_panels = data.get("crewPanels", [])
    aircraft_panels = data.get("aircraftPanels", [])

    if scenario_key == "delay_3hr":
        stats["avgDelayMinutes"] = stats.get("avgDelayMinutes", 0) + 35
        stats["delayed"] = stats.get("delayed", 0) + max(1, len(flights) // 4)
        stats["critical"] = stats.get("critical", 0) + 1
        for flight in flights[:3]:
            flight["status"] = "Extended ATC hold"
            flight["statusCategory"] = "critical"
            flight["delayMinutes"] = flight.get("delayMinutes", 0) + 45
            flight["irregularOps"] = flight.get("irregularOps", {}) or {}
            flight["irregularOps"]["reason"] = "Severe weather cell causing >=3hr delay"
        _add_alert(data, "Severe convection forcing 3hr delay program", level="critical")

    elif scenario_key == "crew_out":
        for flight in flights[:2]:
            flight["crewReady"] = False
            flight["statusCategory"] = "warning"
            flight["status"] = "Crew out of position"
        for panel in crew_panels[:3]:
            panel["readinessState"] = "hold"
            panel["fatigueRisk"] = "high"
            panel["statusNote"] = "What-if: crew reassignment in progress"
        _add_alert(data, "Multiple crews timing out; standby activation required", level="warning")

    elif scenario_key in {"weather_groundstop", "wx_groundstop"}:
        stats["critical"] = stats.get("critical", 0) + 2
        stats["delayed"] = stats.get("delayed", 0) + len(flights) // 2
        for flight in flights:
            flight["statusCategory"] = "warning"
            flight["irregularOps"] = flight.get("irregularOps", {}) or {}
            flight["irregularOps"]["reason"] = "Weather ground stop what-if"
        for plane in aircraft_panels[:2]:
            plane["statusCategory"] = "critical"
            plane["status"] = "Ground stop"
            plane["statusNotes"] = "What-if: Wx ground stop until +120"
        _add_alert(data, "HKG ground stop due to typhoon bands", level="critical")

    data["generatedAt"] = datetime.utcnow().isoformat()
    data["scenario"] = scenario_key
    return data
