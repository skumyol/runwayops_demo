from __future__ import annotations

from typing import Any

from ..config import settings
from ..schemas.reaccommodation import FlightDisruption, FlightManifest, FlightSummary
from .mongo_client import get_client


def _collection(name: str):
    client = get_client()
    return client[settings.mongo_db_name][name]


async def list_flight_summaries() -> list[FlightSummary]:
    collection = _collection(settings.mongo_flight_collection)
    cursor = collection.find({}, {"_id": 0, "summary": 1}).sort("summary.flightNumber", 1)
    summaries: list[FlightSummary] = []
    seen_flights: set[str] = set()
    async for doc in cursor:
        summary = doc.get("summary")
        if summary:
            flight_number = summary.get("flightNumber")
            # Deduplicate by flightNumber to avoid duplicate keys in frontend
            if flight_number and flight_number not in seen_flights:
                seen_flights.add(flight_number)
                summaries.append(FlightSummary.model_validate(summary))
    return summaries


async def fetch_manifest(flight_number: str) -> FlightManifest | None:
    collection = _collection(settings.mongo_flight_collection)
    doc = await collection.find_one(
        {"flightNumber": flight_number.upper()}, {"_id": 0}
    )
    if not doc:
        return None
    return FlightManifest.model_validate(doc)


async def fetch_passengers_for_flight(flight_number: str) -> list[dict[str, Any]]:
    collection = _collection(settings.mongo_passenger_collection)
    cursor = collection.find(
        {"originalFlight": flight_number.upper()}, {"_id": 0}
    ).sort("pnr", 1)
    passengers: list[dict[str, Any]] = []
    async for doc in cursor:
        passengers.append(doc)
    return passengers


async def fetch_passenger(pnr: str) -> dict[str, Any] | None:
    collection = _collection(settings.mongo_passenger_collection)
    return await collection.find_one({"pnr": pnr.upper()}, {"_id": 0})


async def fetch_crew_for_flight(flight_number: str) -> list[dict[str, Any]]:
    collection = _collection(settings.mongo_crew_collection)
    cursor = collection.find(
        {"flightNumber": flight_number.upper()}, {"_id": 0}
    ).sort("rank", 1)
    crew: list[dict[str, Any]] = []
    async for doc in cursor:
        crew.append(doc)
    return crew


async def fetch_disruption(disruption_id: str | None) -> FlightDisruption | None:
    if not disruption_id:
        return None
    collection = _collection(settings.mongo_disruption_collection)
    doc = await collection.find_one({"disruptionId": disruption_id}, {"_id": 0})
    if not doc:
        return None
    return FlightDisruption.model_validate(doc)
