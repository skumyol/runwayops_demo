from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from random import Random
from typing import Any, Dict, List, Optional

import httpx

from ..exceptions import ProviderConfigError, ProviderDataError
from .base import FlightMonitorProvider
from .shared import (
    HKT,
    STATUS_LABELS,
    iso_utc,
    seeded_rng,
    trend_series,
)

AIRCRAFT_CAPACITY = {
    "A35K": 334,
    "A359": 311,
    "A350": 311,
    "77W": 275,
    "B77W": 275,
    "B77X": 301,
    "A333": 251,
    "A332": 251,
    "A321": 202,
    "A21N": 202,
    "A320": 168,
}

PROGRESS_MILESTONES = [
    "Crew inbound",
    "Turn clean",
    "Fuel",
    "Boarding",
    "Pushback",
]


class AviationStackMonitorProvider(FlightMonitorProvider):
    mode = "realtime"

    def __init__(self, api_key: Optional[str], base_url: str) -> None:
        if not api_key:
            raise ProviderConfigError(
                "Realtime mode requires AVIATIONSTACK_API_KEY to be set"
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def get_payload(self, airport: str, carrier: str) -> Dict[str, Any]:
        params = {
            "access_key": self.api_key,
            "dep_iata": airport,
            "airline_iata": carrier,
            "flight_status": "scheduled,active",
            "limit": 25,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.base_url}/flights", params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderDataError(
                f"Upstream API returned {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderDataError("Unable to reach aviationstack API") from exc

        if payload.get("error"):
            message = payload["error"].get("message", "Unknown aviationstack error")
            raise ProviderDataError(message)

        flights_raw = payload.get("data") or []
        if not flights_raw:
            raise ProviderDataError("No realtime flights returned for that filter")

        rng = seeded_rng()
        flights: List[Dict[str, Any]] = []
        alerts: List[Dict[str, Any]] = []

        stats = {
            "totalFlights": 0,
            "onTime": 0,
            "delayed": 0,
            "critical": 0,
            "avgDelayMinutes": 0.0,
            "paxImpacted": 0,
            "crewReadyRate": 0.0,
            "aircraftReadyRate": 0.0,
            "turnReliability": 0.0,
        }
        crew_panels_note = (
            "Crew roster details are only available in synthetic or Mongo modes."
        )
        aircraft_panels_note = (
            "Fleet readiness metadata requires the synthetic or Mongo providers."
        )

        delay_accumulator = 0.0
        crew_ready = 0
        aircraft_ready = 0
        turn_sum = 0.0
        timezone_label = "Asia/Hong_Kong"

        now = datetime.now(tz=UTC)

        for record in flights_raw:
            flight = _transform_record(record, now, rng)
            if not flight:
                continue

            timezone_label = flight.get("timezone", timezone_label)
            stats["totalFlights"] += 1
            if flight["statusCategory"] == "normal":
                stats["onTime"] += 1
            else:
                stats["delayed"] += 1
                delay_accumulator += flight["delayMinutes"]
                if flight["statusCategory"] == "critical":
                    stats["critical"] += 1

            stats["paxImpacted"] += flight["paxImpacted"]
            crew_ready += 1 if flight["crewReady"] else 0
            aircraft_ready += 1 if flight["aircraftReady"] else 0
            turn_sum += flight["turnProgress"] / 100

            flights.append(flight)

            if flight["statusCategory"] != "normal":
                alerts.append(
                    {
                        "level": flight["statusCategory"],
                        "flightNumber": flight["flightNumber"],
                        "message": flight["status"],
                        "gate": flight["gate"],
                        "delayMinutes": flight["delayMinutes"],
                        "paxImpacted": flight["paxImpacted"],
                        "recommendedAction": flight["irregularOps"]["actions"][0],
                    }
                )

        if not flights:
            raise ProviderDataError("Realtime API returned no usable flights")

        stats["avgDelayMinutes"] = (
            round(delay_accumulator / stats["delayed"], 1) if stats["delayed"] else 0
        )
        stats["crewReadyRate"] = round(crew_ready / stats["totalFlights"], 2)
        stats["aircraftReadyRate"] = round(aircraft_ready / stats["totalFlights"], 2)
        stats["turnReliability"] = round(turn_sum / stats["totalFlights"], 2)

        trend_rng = seeded_rng()
        trend = {
            "movementsPerHour": trend_series(48, 4, 6, trend_rng),
            "avgDelay": trend_series(
                max(stats["avgDelayMinutes"], 8), 5, 6, trend_rng
            ),
            "loadFactor": trend_series(88, 1.8, 6, trend_rng),
        }

        return {
            "mode": "realtime",
            "airport": airport,
            "carrier": carrier,
            "timezone": timezone_label,
            "generatedAt": iso_utc(datetime.now(tz=HKT)),
            "nextUpdateSeconds": 30,
            "stats": stats,
            "alerts": alerts,
            "flights": flights,
            "trend": trend,
            "crewPanels": [],
            "aircraftPanels": [],
            "crewPanelsNote": crew_panels_note,
            "aircraftPanelsNote": aircraft_panels_note,
        }


def _transform_record(
    record: Dict[str, Any], now: datetime, rng: Random
) -> Optional[Dict[str, Any]]:
    flight_info = record.get("flight") or {}
    departure = record.get("departure") or {}
    arrival = record.get("arrival") or {}
    aircraft = record.get("aircraft") or {}
    airline = record.get("airline") or {}

    number = flight_info.get("iata") or flight_info.get("number")
    if not number:
        return None

    scheduled_dep = _parse_dt(departure.get("scheduled")) or now
    estimated_dep = _parse_dt(departure.get("estimated")) or scheduled_dep
    estimated_arrival = _parse_dt(arrival.get("estimated")) or _parse_dt(
        arrival.get("scheduled")
    ) or (estimated_dep + timedelta(hours=12))

    tz = scheduled_dep.tzinfo.tzname(scheduled_dep) if scheduled_dep.tzinfo else "UTC"

    delay_minutes = departure.get("delay")
    if delay_minutes is None:
        delay_minutes = max(
            0, round((estimated_dep - scheduled_dep).total_seconds() / 60.0)
        )

    status_text = record.get("flight_status", "scheduled").replace("_", " ").title()
    status_category = _status_category(delay_minutes)
    status_display = (
        status_text if status_category != "normal" else "On track"
    )

    aircraft_code = aircraft.get("iata") or aircraft.get("icao") or ""
    capacity = AIRCRAFT_CAPACITY.get(aircraft_code.upper(), 260)
    pax_impacted = int(capacity * 0.25) if status_category != "normal" else 0

    turn_progress = _turn_progress(scheduled_dep, now)
    milestones = _milestones(turn_progress)
    connections = _connections_snapshot(capacity, rng)
    load_factor = round(rng.uniform(0.78, 0.97), 2)

    baggage_status = (
        "Closed"
        if turn_progress > 85
        else "Loading"
        if turn_progress > 60
        else "Staging"
    )
    fuel_status = (
        "Complete"
        if turn_progress > 80
        else "In progress"
        if turn_progress > 40
        else "Queued"
    )

    irregular_reason = (
        f"{status_text} — monitoring impact on {airline.get('name', '').strip() or 'CX'} network"
    )
    irregular_actions = _irregular_actions(status_category, number)

    crew_ready = turn_progress > 30
    aircraft_ready = turn_progress > 55
    ground_ready = turn_progress > 45

    return {
        "flightNumber": number,
        "route": f"{departure.get('iata', 'HKG')} → {arrival.get('iata', '???')}",
        "destination": arrival.get("airport", "Unknown"),
        "status": status_display,
        "statusCategory": status_category,
        "statusColor": STATUS_LABELS[status_category]["color"],
        "scheduledDeparture": iso_utc(scheduled_dep),
        "estimatedDeparture": iso_utc(estimated_dep),
        "estimatedArrival": iso_utc(estimated_arrival),
        "gate": departure.get("gate", "TBD"),
        "standbyGate": departure.get("terminal", "Main"),
        "tailNumber": aircraft.get("registration", "TBD"),
        "aircraft": aircraft.get("icao", "Fleet") or aircraft.get("iata", "Fleet"),
        "paxCount": capacity,
        "premiumPax": int(capacity * 0.22),
        "loadFactor": load_factor,
        "connections": connections,
        "delayMinutes": delay_minutes,
        "turnProgress": turn_progress,
        "crewReady": crew_ready,
        "aircraftReady": aircraft_ready,
        "groundReady": ground_ready,
        "paxImpacted": pax_impacted,
        "irregularOps": {
            "reason": irregular_reason,
            "actions": irregular_actions,
        },
        "milestones": milestones,
        "baggageStatus": baggage_status,
        "fuelStatus": fuel_status,
        "lastUpdated": iso_utc(now.astimezone(HKT)),
        "timezone": tz,
    }


def _parse_dt(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _status_category(delay: int) -> str:
    if delay >= 45:
        return "critical"
    if delay >= 15:
        return "warning"
    return "normal"


def _turn_progress(scheduled: datetime, now: datetime) -> float:
    prep_start = scheduled - timedelta(minutes=120)
    total = (scheduled - prep_start).total_seconds()
    if now <= prep_start:
        return 5.0
    if now >= scheduled:
        return 99.0
    elapsed = (now - prep_start).total_seconds()
    progress = max(5.0, min(99.0, (elapsed / total) * 100))
    return round(progress, 1)


def _milestones(progress: float) -> List[Dict[str, str]]:
    buckets = []
    for index, label in enumerate(PROGRESS_MILESTONES):
        threshold = (index + 1) * (100 / len(PROGRESS_MILESTONES))
        if progress >= threshold + 10:
            state = "complete"
        elif progress >= threshold - 10:
            state = "active"
        else:
            state = "pending"
        buckets.append({"label": label, "state": state})
    return buckets


def _connections_snapshot(capacity: int, rng: Random) -> Dict[str, int]:
    tight = rng.randint(4, 18)
    missed = rng.randint(0, 6)
    vip = rng.randint(0, 6)
    return {"tight": tight, "missed": missed, "vip": vip}


def _irregular_actions(status: str, number: str) -> List[str]:
    if status == "critical":
        return [
            f"Consider swapping equipment for {number}",
            "Hold premium inventory for reprotect",
            "Coordinate with IOC for contingency slot",
        ]
    if status == "warning":
        return [
            "Ping crew control for readiness update",
            "Alert lounges about potential delay",
            "Pre-stage vouchers in CX App",
        ]
    return [
        "Monitor weather build-up around PRD",
        "Keep 4 seats open for late reprotect",
        "Share ETA with airport duty manager",
    ]
