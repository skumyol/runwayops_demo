from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import Random
from typing import Any, Dict, Iterable, List, Mapping, Sequence, TypedDict

HKT = timezone(timedelta(hours=8))

STATUS_LABELS = {
    "normal": {"label": "On track", "color": "#059669"},
    "warning": {"label": "Attention", "color": "#b45309"},
    "critical": {"label": "Critical", "color": "#b91c1c"},
}


class CrewPanel(TypedDict):
    employeeId: str
    name: str
    rank: str
    flightNumber: str
    aircraftType: str
    tailNumber: str | None
    dutyStatus: str
    readinessState: str
    currentDutyPhase: str
    fatigueRisk: str
    fdpRemainingHours: float
    base: str
    contactPhone: str | None
    contactEmail: str | None
    availabilityNote: str | None
    statusNote: str | None
    commsPreference: str | None
    lastUpdated: str | None


class AircraftPanel(TypedDict):
    tailNumber: str
    type: str
    status: str
    statusCategory: str
    statusColor: str
    flightNumber: str | None
    gate: str | None
    standbyGate: str | None
    nextDeparture: str | None
    lastACheck: str | None
    lastCCheck: str | None
    statusNotes: str | None
    lastUpdated: str | None

def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def seeded_rng(window_seconds: int = 30) -> Random:
    epoch_bucket = int(datetime.utcnow().timestamp() // window_seconds)
    return Random(epoch_bucket)


def trend_series(base: float, variance: float, points: int, rng: Random) -> List[float]:
    values: List[float] = []
    current = base
    for _ in range(points):
        current = max(0, current + rng.uniform(-variance, variance))
        values.append(round(current, 2))
    return values


def crew_panels_from_docs(
    flights: Sequence[Mapping[str, Any]], crew_docs: Iterable[Mapping[str, Any]]
) -> List[CrewPanel]:
    flight_lookup: Dict[str, Mapping[str, Any]] = {
        flight.get("flightNumber"): flight for flight in flights if flight.get("flightNumber")
    }
    panels: List[CrewPanel] = []
    for doc in crew_docs:
        employee_id = doc.get("employeeId")
        flight_number = doc.get("flightNumber")
        if not employee_id or not flight_number:
            continue
        flight = flight_lookup.get(flight_number)
        if not flight:
            # Only surface crew tied to the flights currently rendered.
            continue
        assignment = doc.get("assignment") or {}
        duty = doc.get("duty") or {}
        availability = doc.get("availability") or {}
        contact = doc.get("contact") or {}
        readiness = doc.get("readinessState") or (
            "ready" if assignment.get("status") == "ON_DUTY" else "standby"
        )
        panels.append(
            {
                "employeeId": employee_id,
                "name": f"{doc.get('firstName', '').strip()} {doc.get('lastName', '').strip()}".strip(),
                "rank": doc.get("rank", "FA"),
                "flightNumber": flight_number,
                "aircraftType": assignment.get("aircraftType") or flight.get("aircraft", ""),
                "tailNumber": assignment.get("aircraftRegistration") or flight.get("tailNumber"),
                "dutyStatus": assignment.get("status", "STANDBY"),
                "readinessState": readiness,
                "currentDutyPhase": doc.get("currentDutyPhase", "Standby"),
                "fatigueRisk": doc.get("fatigueRisk", "medium"),
                "fdpRemainingHours": float(duty.get("fdpRemainingHours", 0.0)),
                "base": doc.get("base", "HKG"),
                "contactPhone": contact.get("phone"),
                "contactEmail": contact.get("email"),
                "availabilityNote": availability.get("earliestAvailable"),
                "statusNote": doc.get("statusNote"),
                "commsPreference": doc.get("commsPreference"),
                "lastUpdated": (doc.get("_metadata") or {}).get("lastUpdated"),
            }
        )
    panels.sort(key=lambda item: (item["flightNumber"], item["rank"]))
    return panels


def aircraft_panels_from_docs(
    flights: Sequence[Mapping[str, Any]], fleet_docs: Iterable[Mapping[str, Any]]
) -> List[AircraftPanel]:
    tail_lookup: Dict[str, Mapping[str, Any]] = {
        (flight.get("tailNumber") or "").upper(): flight
        for flight in flights
        if flight.get("tailNumber")
    }
    panels: List[AircraftPanel] = []
    for doc in fleet_docs:
        tail = (doc.get("registration") or "").upper()
        if not tail:
            continue
        flight = tail_lookup.get(tail)
        if not flight:
            # Skip aircraft that are not currently tied to the departure bank.
            continue
        status = doc.get("status", "ACTIVE")
        status_category = _status_category_for_aircraft(status)
        panels.append(
            {
                "tailNumber": tail,
                "type": doc.get("type", "Fleet"),
                "status": status,
                "statusCategory": status_category,
                "statusColor": STATUS_LABELS[status_category]["color"],
                "flightNumber": flight.get("flightNumber"),
                "gate": flight.get("gate"),
                "standbyGate": flight.get("standbyGate"),
                "nextDeparture": flight.get("scheduledDeparture"),
                "lastACheck": doc.get("lastACheck"),
                "lastCCheck": doc.get("lastCCheck"),
                "statusNotes": doc.get("statusNotes"),
                "lastUpdated": (doc.get("_metadata") or {}).get("lastUpdated"),
            }
        )
    panels.sort(key=lambda item: item["tailNumber"])
    return panels


def _status_category_for_aircraft(status: str) -> str:
    normalized = (status or "").upper()
    if normalized in {"ACTIVE"}:
        return "normal"
    if normalized in {"MAINT"}:
        return "warning"
    return "critical"
