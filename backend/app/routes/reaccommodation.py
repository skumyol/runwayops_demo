from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.reaccommodation import (
    CrewMember,
    FlightManifestResponse,
    FlightQueueResponse,
    PassengerDetail,
    PassengerDetailResponse,
    PassengerSummary,
    TierType,
)
from ..services import reaccommodation as data_service

router = APIRouter(prefix="/api/reaccommodation", tags=["reaccommodation"])

ALLOWED_TIERS: set[str] = {"Green", "Silver", "Gold", "Diamond"}


def _resolve_tier(value: str | None) -> TierType:
    if value in ALLOWED_TIERS:
        return value  # type: ignore[return-value]
    return "Green"


def _passenger_name(doc: dict) -> str:
    personal = (doc.get("basePassenger") or {}).get("personalDetails") or {}
    first = personal.get("firstName", "")
    last = personal.get("lastName", "")
    full = f"{first} {last}".strip()
    return full or doc.get("pnr", "Unknown")


def _passenger_summary(doc: dict) -> PassengerSummary:
    name = _passenger_name(doc)
    tier = _resolve_tier(
        ((doc.get("cathayProfile") or {}).get("loyaltyProgram") or {}).get("tier")
    )
    return PassengerSummary(
        pnr=doc.get("pnr", ""),
        name=name,
        tier=tier,
        cabin=doc.get("cabin", "Y"),
        value=int(doc.get("revenueValue", 0)),
        ssrs=list(doc.get("ssrs", [])),
        contact=doc.get("contact", ""),
        originalFlight=doc.get("originalFlight", ""),
        originalRoute=doc.get("originalRoute", ""),
        originalTime=doc.get("originalTime", ""),
        isPRM=bool(doc.get("isPRM", False)),
        hasInfant=bool(doc.get("hasInfant", False)),
        hasFamily=bool(doc.get("hasFamily", False)),
    )


def _passenger_detail(doc: dict) -> PassengerDetail:
    summary = _passenger_summary(doc)
    return PassengerDetail(
        **summary.model_dump(),
        basePassenger=doc.get("basePassenger", {}),
        cathayProfile=doc.get("cathayProfile", {}),
        disruptionContext=doc.get("disruptionContext", {}),
        metadata=doc.get("metadata", {}),
    )


@router.get("/flights", response_model=FlightQueueResponse)
async def list_flights() -> FlightQueueResponse:
    flights = await data_service.list_flight_summaries()
    return FlightQueueResponse(flights=flights)


@router.get("/flights/{flight_number}/manifest", response_model=FlightManifestResponse)
async def get_manifest(flight_number: str) -> FlightManifestResponse:
    manifest = await data_service.fetch_manifest(flight_number)
    if not manifest:
        raise HTTPException(status_code=404, detail="Flight manifest not found")
    passengers_raw = await data_service.fetch_passengers_for_flight(
        manifest.flightNumber
    )
    crew_raw = await data_service.fetch_crew_for_flight(manifest.flightNumber)
    disruption = await data_service.fetch_disruption(manifest.disruptionId)
    passengers = [_passenger_summary(doc) for doc in passengers_raw]
    crew = [CrewMember.model_validate(doc) for doc in crew_raw]
    return FlightManifestResponse(
        manifest=manifest,
        passengers=passengers,
        crew=crew,
        disruption=disruption,
    )


@router.get("/passengers/{pnr}", response_model=PassengerDetailResponse)
async def get_passenger_detail(pnr: str) -> PassengerDetailResponse:
    passenger_doc = await data_service.fetch_passenger(pnr)
    if not passenger_doc:
        raise HTTPException(status_code=404, detail="Passenger not found")

    manifest = await data_service.fetch_manifest(passenger_doc.get("originalFlight", ""))
    crew_docs = (
        await data_service.fetch_crew_for_flight(manifest.flightNumber)
        if manifest
        else []
    )
    passenger = _passenger_detail(passenger_doc)

    return PassengerDetailResponse(
        passenger=passenger,
        flight=manifest.summary if manifest else None,
        options=manifest.options if manifest else [],
        crew=[CrewMember.model_validate(doc) for doc in crew_docs],
    )
