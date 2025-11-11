from __future__ import annotations

from datetime import datetime, timedelta
from random import Random
from typing import Any, Dict, List, Tuple

from .base import FlightMonitorProvider
from .shared import HKT, STATUS_LABELS, iso_utc, seeded_rng, trend_series


class SyntheticMonitorProvider(FlightMonitorProvider):
    mode = "synthetic"

    async def get_payload(self, airport: str, carrier: str) -> Dict[str, Any]:
        return build_monitor_payload(airport, carrier)


BASE_FLIGHTS: List[Dict[str, Any]] = [
    {
        "flightNumber": "CX520",
        "route": "HKG → NRT",
        "destination": "Tokyo Narita",
        "aircraft": "Airbus A350-900",
        "tailNumber": "B-LRG",
        "gate": "N65",
        "standbyGate": "N67",
        "scheduled_offset": 35,
        "base_delay": 32,
        "delay_jitter": 8,
        "turn_progress": 0.46,
        "paxCount": 284,
        "premiumPax": 54,
        "loadFactor": 0.92,
        "connections": {"tight": 18, "missed": 6, "vip": 4},
        "flags": {"crewReady": False, "aircraftReady": True, "groundReady": True},
        "statusText": "Gate hold (ATC flow)",
        "statusCategory": "critical",
        "impactRatio": 0.34,
        "blockMinutes": 245,
        "baggageStatus": "Loaded 78%",
        "fuelStatus": "Complete",
        "irregularOps": {
            "reason": "Northbound ATC slot programme",
            "actions": [
                "Request slot swap with CX524",
                "Standby bus gate if hold exceeds 40 min",
                "Reprotect 11 J pax via JL704",
            ],
        },
        "milestones": [
            {"label": "Crew inbound", "state": "complete"},
            {"label": "Catering", "state": "complete"},
            {"label": "Boarding", "state": "active"},
            {"label": "Door close", "state": "pending"},
            {"label": "Pushback", "state": "pending"},
        ],
        "alert": "ATC slot pushed by 30 min — evaluate CX524 consolidation",
    },
    {
        "flightNumber": "CX255",
        "route": "HKG → LHR",
        "destination": "London Heathrow",
        "aircraft": "Airbus A350-1000",
        "tailNumber": "B-LXI",
        "gate": "W22",
        "standbyGate": "W30",
        "scheduled_offset": 80,
        "base_delay": 18,
        "delay_jitter": 6,
        "turn_progress": 0.58,
        "paxCount": 312,
        "premiumPax": 74,
        "loadFactor": 0.95,
        "connections": {"tight": 24, "missed": 4, "vip": 6},
        "flags": {"crewReady": True, "aircraftReady": True, "groundReady": False},
        "statusText": "Crew step-off waiting on MX release",
        "statusCategory": "warning",
        "impactRatio": 0.28,
        "blockMinutes": 780,
        "baggageStatus": "Belt 5 loading",
        "fuelStatus": "In progress",
        "irregularOps": {
            "reason": "Inbound aircraft minor MX clearance",
            "actions": [
                "Swap to tail B-LXB if release >25 min",
                "Prioritise J/F catering reload",
                "Alert oneworld lounge for potential hold",
            ],
        },
        "milestones": [
            {"label": "Crew inbound", "state": "complete"},
            {"label": "Cleaning", "state": "complete"},
            {"label": "Fuel", "state": "active"},
            {"label": "Boarding", "state": "pending"},
            {"label": "Pushback", "state": "pending"},
        ],
        "alert": "Awaiting MX release on CX255 — heavy premium load",
    },
    {
        "flightNumber": "CX865",
        "route": "HKG → SFO",
        "destination": "San Francisco",
        "aircraft": "Boeing 777-300ER",
        "tailNumber": "B-KPY",
        "gate": "N312",
        "standbyGate": "N510",
        "scheduled_offset": 120,
        "base_delay": 12,
        "delay_jitter": 5,
        "turn_progress": 0.39,
        "paxCount": 276,
        "premiumPax": 48,
        "loadFactor": 0.88,
        "connections": {"tight": 12, "missed": 2, "vip": 3},
        "flags": {"crewReady": True, "aircraftReady": False, "groundReady": True},
        "statusText": "Awaiting arriving crew duty handoff",
        "statusCategory": "warning",
        "impactRatio": 0.22,
        "blockMinutes": 720,
        "baggageStatus": "Bags staged",
        "fuelStatus": "Queued",
        "irregularOps": {
            "reason": "Crew duty window squeeze",
            "actions": [
                "Stage relief crew in standby room",
                "Trigger proactive rebook for 22 premium pax",
                "Alert SFO station on potential late arrival",
            ],
        },
        "milestones": [
            {"label": "Crew inbound", "state": "active"},
            {"label": "Fuel", "state": "pending"},
            {"label": "Catering", "state": "pending"},
            {"label": "Boarding", "state": "pending"},
            {"label": "Pushback", "state": "pending"},
        ],
        "alert": "Duty limits for CX865 crew in 50 min",
    },
    {
        "flightNumber": "CX903",
        "route": "HKG → MNL",
        "destination": "Manila",
        "aircraft": "Airbus A321neo",
        "tailNumber": "B-HSM",
        "gate": "E15",
        "standbyGate": "E17",
        "scheduled_offset": 25,
        "base_delay": 0,
        "delay_jitter": 2,
        "turn_progress": 0.73,
        "paxCount": 198,
        "premiumPax": 22,
        "loadFactor": 0.81,
        "connections": {"tight": 6, "missed": 0, "vip": 1},
        "flags": {"crewReady": True, "aircraftReady": True, "groundReady": True},
        "statusText": "On schedule",
        "statusCategory": "normal",
        "impactRatio": 0.05,
        "blockMinutes": 140,
        "baggageStatus": "Closed",
        "fuelStatus": "Complete",
        "irregularOps": {
            "reason": "No active disruption",
            "actions": [
                "Monitor convection build-up south of PRC",
                "Hold spare crew for return CX900",
                "Keep 4 Y seats open for misconnects",
            ],
        },
        "milestones": [
            {"label": "Crew inbound", "state": "complete"},
            {"label": "Turn clean", "state": "complete"},
            {"label": "Boarding", "state": "active"},
            {"label": "Door close", "state": "pending"},
            {"label": "Pushback", "state": "pending"},
        ],
        "alert": "",
    },
    {
        "flightNumber": "CX315",
        "route": "HKG → CDG",
        "destination": "Paris Charles de Gaulle",
        "aircraft": "Airbus A350-900",
        "tailNumber": "B-LRB",
        "gate": "W19",
        "standbyGate": "W21",
        "scheduled_offset": 140,
        "base_delay": 48,
        "delay_jitter": 10,
        "turn_progress": 0.33,
        "paxCount": 268,
        "premiumPax": 51,
        "loadFactor": 0.9,
        "connections": {"tight": 16, "missed": 5, "vip": 3},
        "flags": {"crewReady": False, "aircraftReady": False, "groundReady": True},
        "statusText": "Awaiting ETOPS release",
        "statusCategory": "critical",
        "impactRatio": 0.31,
        "blockMinutes": 740,
        "baggageStatus": "On hold",
        "fuelStatus": "Not started",
        "irregularOps": {
            "reason": "Lightning strike inspection",
            "actions": [
                "Tech log review with Airbus hotline",
                "Source replacement aircraft from CX317",
                "Notify premium services of >45 min delay",
            ],
        },
        "milestones": [
            {"label": "Crew inbound", "state": "pending"},
            {"label": "MX release", "state": "active"},
            {"label": "Fuel", "state": "pending"},
            {"label": "Boarding", "state": "pending"},
            {"label": "Pushback", "state": "pending"},
        ],
        "alert": "ETOPS release outstanding on CX315",
    },
    {
        "flightNumber": "CX685",
        "route": "HKG → SIN",
        "destination": "Singapore",
        "aircraft": "Airbus A330-300",
        "tailNumber": "B-HLB",
        "gate": "S32",
        "standbyGate": "S34",
        "scheduled_offset": 55,
        "base_delay": 9,
        "delay_jitter": 4,
        "turn_progress": 0.62,
        "paxCount": 214,
        "premiumPax": 28,
        "loadFactor": 0.86,
        "connections": {"tight": 10, "missed": 1, "vip": 2},
        "flags": {"crewReady": True, "aircraftReady": True, "groundReady": False},
        "statusText": "Tight turn — awaiting catering",
        "statusCategory": "warning",
        "impactRatio": 0.18,
        "blockMinutes": 215,
        "baggageStatus": "Load 40%",
        "fuelStatus": "Complete",
        "irregularOps": {
            "reason": "Late catering truck",
            "actions": [
                "Stage spare catering crew at stand 402",
                "Alert SIN for possible 15 min delay",
                "Communicate to VIP concierge desk",
            ],
        },
        "milestones": [
            {"label": "Crew inbound", "state": "complete"},
            {"label": "Turn clean", "state": "active"},
            {"label": "Catering", "state": "active"},
            {"label": "Boarding", "state": "pending"},
            {"label": "Pushback", "state": "pending"},
        ],
        "alert": "Catering delay impacting CX685",
    },
]


def build_monitor_payload(airport: str, carrier: str) -> Dict[str, Any]:
    rng = seeded_rng()
    now = datetime.now(tz=HKT)

    flights: List[Dict[str, Any]] = []
    alerts: List[Dict[str, Any]] = []
    total_delay = 0
    delay_count = 0
    impacted_pax = 0
    crew_ready = 0
    aircraft_ready = 0
    turn_sum = 0.0
    critical = 0
    delayed = 0

    for template in BASE_FLIGHTS:
        scheduled = now + timedelta(minutes=template["scheduled_offset"])
        delay = max(
            0,
            template["base_delay"]
            + rng.randint(-template["delay_jitter"], template["delay_jitter"]),
        )
        estimated = scheduled + timedelta(minutes=delay)
        arrival = estimated + timedelta(minutes=template["blockMinutes"])

        status_category = template["statusCategory"]
        if delay >= 35:
            status_category = "critical"
        elif delay >= 10 and status_category != "critical":
            status_category = "warning"
        elif delay <= 4:
            status_category = "normal"

        if status_category != "normal":
            delayed += 1
            total_delay += delay
            delay_count += 1
        if status_category == "critical":
            critical += 1

        crew_ready += 1 if template["flags"]["crewReady"] else 0
        aircraft_ready += 1 if template["flags"]["aircraftReady"] else 0

        turn_progress = max(
            0.12, min(0.98, template["turn_progress"] + rng.uniform(-0.08, 0.08))
        )
        turn_sum += turn_progress

        pax_impacted = (
            int(template["paxCount"] * template.get("impactRatio", 0.15))
            if status_category != "normal"
            else 0
        )
        impacted_pax += pax_impacted

        flight = {
            "flightNumber": template["flightNumber"],
            "route": template["route"],
            "destination": template["destination"],
            "status": template["statusText"] if status_category != "normal" else "On track",
            "statusCategory": status_category,
            "statusColor": STATUS_LABELS[status_category]["color"],
            "scheduledDeparture": iso_utc(scheduled),
            "estimatedDeparture": iso_utc(estimated),
            "estimatedArrival": iso_utc(arrival),
            "gate": template["gate"],
            "standbyGate": template["standbyGate"],
            "tailNumber": template["tailNumber"],
            "aircraft": template["aircraft"],
            "paxCount": template["paxCount"],
            "premiumPax": template["premiumPax"],
            "loadFactor": round(
                max(0.6, min(0.99, template["loadFactor"] + rng.uniform(-0.03, 0.04))), 2
            ),
            "connections": template["connections"],
            "delayMinutes": delay,
            "turnProgress": round(turn_progress * 100, 1),
            "crewReady": template["flags"]["crewReady"],
            "aircraftReady": template["flags"]["aircraftReady"],
            "groundReady": template["flags"]["groundReady"],
            "paxImpacted": pax_impacted,
            "irregularOps": template["irregularOps"],
            "milestones": template["milestones"],
            "baggageStatus": template["baggageStatus"],
            "fuelStatus": template["fuelStatus"],
            "lastUpdated": iso_utc(datetime.now(tz=HKT)),
        }

        flights.append(flight)

        if status_category != "normal" and template["alert"]:
            alerts.append(
                {
                    "level": status_category,
                    "flightNumber": template["flightNumber"],
                    "message": template["alert"],
                    "gate": template["gate"],
                    "delayMinutes": delay,
                    "paxImpacted": pax_impacted,
                    "recommendedAction": template["irregularOps"]["actions"][0],
                }
            )

    avg_delay = round(total_delay / delay_count, 1) if delay_count else 0
    total_flights = len(flights)

    stats = {
        "totalFlights": total_flights,
        "onTime": total_flights - delayed,
        "delayed": delayed,
        "critical": critical,
        "avgDelayMinutes": avg_delay,
        "paxImpacted": impacted_pax,
        "crewReadyRate": round(crew_ready / total_flights, 2),
        "aircraftReadyRate": round(aircraft_ready / total_flights, 2),
        "turnReliability": round(turn_sum / total_flights, 2),
    }

    rng_trend = seeded_rng()
    trend = {
        "movementsPerHour": trend_series(52, 3, 6, rng_trend),
        "avgDelay": trend_series(max(avg_delay, 6), 4, 6, rng_trend),
        "loadFactor": trend_series(86, 1.5, 6, rng_trend),
    }

    crew_panels = _synthetic_crew_panels(flights, rng)
    aircraft_panels = _synthetic_aircraft_panels(flights)

    payload: Dict[str, Any] = {
        "mode": "synthetic",
        "airport": airport,
        "carrier": carrier,
        "timezone": "Asia/Hong_Kong",
        "generatedAt": iso_utc(datetime.now(tz=HKT)),
        "nextUpdateSeconds": 30,
        "stats": stats,
        "alerts": alerts,
        "flights": flights,
        "trend": trend,
        "crewPanels": crew_panels,
        "aircraftPanels": aircraft_panels,
    }
    return payload


CREW_NAME_POOL: List[Tuple[str, str]] = [
    ("Ada", "Lam"),
    ("Marcus", "Yip"),
    ("Ivy", "Cheung"),
    ("Terence", "Ho"),
    ("Elsa", "Cheng"),
    ("Noelle", "Chu"),
    ("Patrick", "Wong"),
    ("Serena", "Fong"),
    ("Brian", "Yeung"),
    ("Lena", "Kwok"),
]


def _synthetic_crew_panels(flights: List[Dict[str, Any]], rng: Random) -> List[Dict[str, Any]]:
    panels: List[Dict[str, Any]] = []
    now = datetime.now(tz=HKT)
    name_index = 0
    for flight in flights:
        flight_status = flight.get("statusCategory", "normal")
        tail = flight.get("tailNumber")
        phases = ["Report", "Briefing", "Boarding", "Standby", "Rest"]
        ranks = ["CPT", "FO", "PUR", "FA", "FA"]
        for idx, rank in enumerate(ranks):
            first, last = CREW_NAME_POOL[name_index % len(CREW_NAME_POOL)]
            name_index += 1
            duty_status = "ON_DUTY" if idx < 3 else "STANDBY"
            readiness = (
                "hold"
                if flight_status == "critical"
                else "standby"
                if flight_status == "warning" and duty_status != "ON_DUTY"
                else "ready"
            )
            fdp_remaining = round(rng.uniform(3.0, 13.5), 1)
            fatigue = (
                "high"
                if fdp_remaining < 4
                else "medium"
                if fdp_remaining < 7
                else "low"
            )
            phase = phases[(idx + len(flight["flightNumber"])) % len(phases)]
            panels.append(
                {
                    "employeeId": f"CXSYN-{flight['flightNumber']}-{idx}",
                    "name": f"{first} {last}",
                    "rank": rank,
                    "flightNumber": flight["flightNumber"],
                    "aircraftType": flight.get("aircraft", "Fleet"),
                    "tailNumber": tail,
                    "dutyStatus": duty_status,
                    "readinessState": readiness,
                    "currentDutyPhase": phase,
                    "fatigueRisk": fatigue,
                    "fdpRemainingHours": fdp_remaining,
                    "base": "HKG",
                    "contactPhone": "+852 5555 0000",
                    "contactEmail": f"{first.lower()}.{last.lower()}@cathay.com",
                    "availabilityNote": iso_utc(
                        now + timedelta(hours=fdp_remaining + 6)
                    ),
                    "statusNote": flight.get("status"),
                    "commsPreference": rng.choice(["Ops chat", "Phone call", "Signal"]),
                    "lastUpdated": iso_utc(now),
                }
            )
    return panels


def _synthetic_aircraft_panels(flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    panels: List[Dict[str, Any]] = []
    now = datetime.now(tz=HKT)
    for idx, flight in enumerate(flights):
        tail = flight.get("tailNumber")
        if not tail:
            continue
        status_category = flight.get("statusCategory", "normal")
        status = (
            "ACTIVE"
            if status_category == "normal"
            else "MAINT"
            if status_category == "warning"
            else "AOG"
        )
        panels.append(
            {
                "tailNumber": tail,
                "type": flight.get("aircraft", "Fleet"),
                "status": status,
                "statusCategory": status_category,
                "statusColor": STATUS_LABELS[status_category]["color"],
                "flightNumber": flight.get("flightNumber"),
                "gate": flight.get("gate"),
                "standbyGate": flight.get("standbyGate"),
                "nextDeparture": flight.get("scheduledDeparture"),
                "lastACheck": iso_utc(now - timedelta(days=45 + idx)),
                "lastCCheck": iso_utc(now - timedelta(days=210 + idx * 3)),
                "statusNotes": flight.get("status"),
                "lastUpdated": flight.get("lastUpdated"),
            }
        )
    return panels
