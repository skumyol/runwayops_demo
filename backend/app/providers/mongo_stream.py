from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from ..config import settings
from ..exceptions import ProviderDataError
from ..services import mongo_client
from .base import FlightMonitorProvider
from .shared import (
    HKT,
    aircraft_panels_from_docs,
    crew_panels_from_docs,
    iso_utc,
    seeded_rng,
    trend_series,
)


class MongoMonitorProvider(FlightMonitorProvider):
    mode = "mongo"

    async def get_payload(self, airport: str, carrier: str) -> Dict[str, Any]:
        client = mongo_client.get_client()
        collection = client[settings.mongo_db_name][
            settings.mongo_flight_instance_collection
        ]
        query = {
            "departureAirport.iata": airport.upper(),
            "flightNumber": {"$regex": f"^{carrier.upper()}"},
        }
        cursor = collection.find(query, {"_id": 0}).sort("scheduledDeparture", 1)
        records = await cursor.to_list(length=None)
        if not records:
            raise ProviderDataError("No Mongo-backed flights for that filter")

        flights = [dict(record) for record in records]
        stats = _compute_stats(flights)
        alerts = _alerts_from_flights(flights)

        rng = seeded_rng()
        avg_delay = max(stats["avgDelayMinutes"], 5)
        avg_load = int(
            100
            * (
                sum(f.get("loadFactor", 0.0) for f in flights)
                / max(len(flights), 1)
            )
        )
        trend = {
            "movementsPerHour": trend_series(max(stats["totalFlights"], 5), 4, 6, rng),
            "avgDelay": trend_series(avg_delay, 3, 6, rng),
            "loadFactor": trend_series(max(avg_load, 60), 2, 6, rng),
        }

        crew_collection = client[settings.mongo_db_name][settings.mongo_crew_collection]
        crew_cursor = crew_collection.find(
            {"flightNumber": {"$in": [flight["flightNumber"] for flight in flights]}},
            {"_id": 0},
        )
        crew_docs = await crew_cursor.to_list(length=None)
        crew_panels = crew_panels_from_docs(flights, crew_docs)
        crew_panels_note = (
            None
            if crew_panels
            else "No crew roster records matched the current flight filter."
        )

        aircraft_collection = client[settings.mongo_db_name][
            settings.mongo_aircraft_collection
        ]
        tail_numbers = [
            flight.get("tailNumber")
            for flight in flights
            if flight.get("tailNumber")
        ]
        aircraft_cursor = aircraft_collection.find(
            {"registration": {"$in": tail_numbers}},
            {"_id": 0},
        )
        aircraft_docs = await aircraft_cursor.to_list(length=None)
        aircraft_panels = aircraft_panels_from_docs(flights, aircraft_docs)
        aircraft_panels_note = (
            None
            if aircraft_panels
            else "No aircraft records found for the current tails."
        )

        timezone_label = flights[0].get("timezone", "Asia/Hong_Kong")
        now = datetime.now(tz=HKT)
        return {
            "mode": "mongo",
            "airport": airport.upper(),
            "carrier": carrier.upper(),
            "timezone": timezone_label,
            "generatedAt": iso_utc(now),
            "nextUpdateSeconds": 30,
            "stats": stats,
            "alerts": alerts,
            "flights": flights,
            "trend": trend,
            "crewPanels": crew_panels,
            "aircraftPanels": aircraft_panels,
            "crewPanelsNote": crew_panels_note,
            "aircraftPanelsNote": aircraft_panels_note,
        }


def _compute_stats(flights: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(flights)
    on_time = sum(1 for flight in flights if flight.get("statusCategory") == "normal")
    delayed = total - on_time
    critical = sum(1 for flight in flights if flight.get("statusCategory") == "critical")

    delay_total = sum(
        flight.get("delayMinutes", 0)
        for flight in flights
        if flight.get("statusCategory") != "normal"
    )
    avg_delay = round(delay_total / delayed, 1) if delayed else 0.0

    pax_impacted = sum(flight.get("paxImpacted", 0) for flight in flights)
    crew_ready = sum(1 for flight in flights if flight.get("crewReady"))
    aircraft_ready = sum(1 for flight in flights if flight.get("aircraftReady"))
    turn_sum = sum(flight.get("turnProgress", 0) for flight in flights)

    return {
        "totalFlights": total,
        "onTime": on_time,
        "delayed": delayed,
        "critical": critical,
        "avgDelayMinutes": avg_delay,
        "paxImpacted": pax_impacted,
        "crewReadyRate": round(crew_ready / total, 2) if total else 0.0,
        "aircraftReadyRate": round(aircraft_ready / total, 2) if total else 0.0,
        "turnReliability": round((turn_sum / total) / 100, 2) if total else 0.0,
    }


def _alerts_from_flights(flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for flight in flights:
        if flight.get("statusCategory") == "normal":
            continue
        irregular = flight.get("irregularOps") or {}
        actions = irregular.get("actions") or []
        alerts.append(
            {
                "level": flight.get("statusCategory", "warning"),
                "flightNumber": flight.get("flightNumber", "UNK"),
                "message": flight.get("status", ""),
                "gate": flight.get("gate", "TBD"),
                "delayMinutes": flight.get("delayMinutes", 0),
                "paxImpacted": flight.get("paxImpacted", 0),
                "recommendedAction": actions[0] if actions else "Monitor situation",
            }
        )
    return alerts
