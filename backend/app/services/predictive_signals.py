"""Shared predictive signal helper for disruption detection.

This module centralizes the heuristic logic used by the predictive node so
that both the LangGraph workflow and normal flight monitor responses can
surface consistent insight. The scorer intentionally references weather,
aircraft, and crew readiness indicators to match dashboard requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


WEATHER_KEYWORDS = (
    "weather",
    "storm",
    "typhoon",
    "rain",
    "wx",
    "wind",
    "turbulence",
)


@dataclass
class SignalBreakdown:
    """Typed helper used internally while computing risk contributions."""

    score: float
    evidence: str
    impact_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "evidence": self.evidence,
            "impact_count": self.impact_count,
        }


def _clamp(value: float, minimum: float = 0.0, maximum: float = 0.98) -> float:
    return max(minimum, min(maximum, value))


def _keyword_hits(items: List[str]) -> Tuple[int, List[str]]:
    hits = []
    for text in items:
        low_text = text.lower()
        for keyword in WEATHER_KEYWORDS:
            if keyword in low_text:
                hits.append(text)
                break
    return len(hits), hits[:3]


def _score_weather(data: Dict[str, Any]) -> SignalBreakdown:
    alerts = data.get("alerts", [])
    flights = data.get("flights", [])
    alert_hits, samples = _keyword_hits([alert.get("message", "") for alert in alerts])
    flight_hits, _ = _keyword_hits([
        (flight.get("irregularOps", {}) or {}).get("reason", "")
        for flight in flights
    ])

    raw_score = 0.15 * alert_hits + 0.1 * flight_hits
    avg_delay = (data.get("stats", {}) or {}).get("avgDelayMinutes", 0)
    raw_score += min(0.3, avg_delay / 120)

    evidence = "Clear" if (alert_hits + flight_hits) == 0 else ", ".join(samples) or "Multiple weather alerts"
    impact = alert_hits + flight_hits
    level = SignalBreakdown(score=_clamp(raw_score), evidence=evidence, impact_count=impact)
    return level


def _score_crew(data: Dict[str, Any]) -> SignalBreakdown:
    flights = data.get("flights", [])
    crew_panels = data.get("crewPanels", [])

    flights_not_ready = sum(1 for flight in flights if not flight.get("crewReady", True))
    fatigue_hits = sum(1 for panel in crew_panels if panel.get("fatigueRisk") == "high")
    standby_needed = sum(1 for panel in crew_panels if panel.get("readinessState") == "hold")

    raw_score = 0.2 * flights_not_ready + 0.1 * fatigue_hits + 0.05 * standby_needed
    total_crews = max(1, len(crew_panels))
    utilization = 1 - (standby_needed / total_crews)
    raw_score += max(0, 0.25 - utilization * 0.25)

    evidence_parts = []
    if flights_not_ready:
        evidence_parts.append(f"{flights_not_ready} flights waiting on crew")
    if fatigue_hits:
        evidence_parts.append(f"{fatigue_hits} crews high fatigue")
    if standby_needed:
        evidence_parts.append(f"{standby_needed} in standby/hold")
    evidence = ", ".join(evidence_parts) or "All crews ready"

    return SignalBreakdown(score=_clamp(raw_score), evidence=evidence, impact_count=flights_not_ready)


def _score_aircraft(data: Dict[str, Any]) -> SignalBreakdown:
    flights = data.get("flights", [])
    aircraft_panels = data.get("aircraftPanels", [])

    aircraft_not_ready = sum(1 for flight in flights if not flight.get("aircraftReady", True))
    mx_holds = sum(1 for plane in aircraft_panels if (plane.get("statusCategory") or "").lower() != "normal")

    raw_score = 0.2 * aircraft_not_ready + 0.15 * mx_holds
    evidence_parts = []
    if aircraft_not_ready:
        evidence_parts.append(f"{aircraft_not_ready} flights without cleared tails")
    if mx_holds:
        evidence_parts.append(f"{mx_holds} aircraft flagged in MX queue")
    evidence = ", ".join(evidence_parts) or "All aircraft released"

    return SignalBreakdown(score=_clamp(raw_score), evidence=evidence, impact_count=aircraft_not_ready or mx_holds)


def compute_predictive_signals(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return disruption probability plus weather/crew/aircraft breakdown."""

    stats = data.get("stats", {}) or {}
    total = max(1, stats.get("totalFlights", 1))
    delayed_ratio = stats.get("delayed", 0) / total
    critical_ratio = stats.get("critical", 0) / total

    weather = _score_weather(data)
    crew = _score_crew(data)
    aircraft = _score_aircraft(data)

    weighted = (
        0.4 * weather.score
        + 0.3 * crew.score
        + 0.3 * aircraft.score
        + 0.15 * delayed_ratio
        + 0.25 * critical_ratio
    )
    risk_probability = _clamp(weighted)
    detected = risk_probability >= 0.6 or critical_ratio > 0.15

    reasoning = (
        f"Weather: {weather.evidence}. "
        f"Aircraft: {aircraft.evidence}. "
        f"Crew: {crew.evidence}."
    )

    return {
        "disruption_detected": detected,
        "risk_probability": risk_probability,
        "reasoning": reasoning,
        "metrics": {
            "total_flights": total,
            "delayed_flights": stats.get("delayed", 0),
            "critical_flights": stats.get("critical", 0),
            "avg_delay_minutes": stats.get("avgDelayMinutes", 0),
        },
        "signal_breakdown": {
            "weather": weather.to_dict(),
            "aircraft": aircraft.to_dict(),
            "crew": crew.to_dict(),
        },
        "drivers": [
            {"category": "Weather", **weather.to_dict()},
            {"category": "Aircraft", **aircraft.to_dict()},
            {"category": "Crew", **crew.to_dict()},
        ],
    }

