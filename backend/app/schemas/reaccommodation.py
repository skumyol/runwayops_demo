from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

TierType = Literal["Green", "Silver", "Gold", "Diamond"]


class WhyReason(BaseModel):
    text: str
    type: str | None = None


class ReaccommodationOption(BaseModel):
    id: str
    departureTime: str
    arrivalTime: str
    route: str
    cabin: str
    seats: int
    trvScore: int
    arrivalDelta: str | None = None
    badges: list[str] = Field(default_factory=list)
    whyReasons: list[WhyReason] = Field(default_factory=list)


class TierBreakdown(BaseModel):
    tier: TierType
    count: int


class CabinBreakdown(BaseModel):
    cabin: str
    count: int


class CohortPassenger(BaseModel):
    pnr: str
    name: str
    tier: TierType
    defaultOption: str
    confidence: int
    hasException: bool
    notes: str | None = None
    cabin: str


class FlightSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    flightNumber: str
    route: str
    destination: str
    severity: Literal["High", "Medium", "Low"]
    affectedCount: int
    tierBreakdown: list[TierBreakdown]
    cabinBreakdown: list[CabinBreakdown]
    defaultSuitability: int
    exceptions: int
    blockMinutes: int
    aircraft: str
    statusText: str
    updatedAt: str


class FlightManifest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    flightNumber: str
    summary: FlightSummary
    passengerIds: list[str]
    crewIds: list[str]
    options: list[ReaccommodationOption]
    cohortPassengers: list[CohortPassenger]
    disruptionId: str | None = None


class PassengerSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pnr: str
    name: str
    tier: TierType
    cabin: str
    value: int
    ssrs: list[str]
    contact: str
    originalFlight: str
    originalRoute: str
    originalTime: str
    isPRM: bool
    hasInfant: bool
    hasFamily: bool


class PassengerDetail(PassengerSummary):
    basePassenger: dict[str, Any]
    cathayProfile: dict[str, Any]
    disruptionContext: dict[str, Any]
    metadata: dict[str, Any]


class CrewMember(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    employeeId: str
    firstName: str
    lastName: str
    rank: str
    base: str
    currentLocation: str
    qualifications: dict[str, Any]
    duty: dict[str, Any]
    assignment: dict[str, Any] | None = None
    availability: dict[str, Any]
    contact: dict[str, Any]
    flightNumber: str
    metadata: dict[str, Any] = Field(default_factory=dict, alias="_metadata")


class FlightDisruption(BaseModel):
    model_config = ConfigDict(extra="ignore")

    disruptionId: str
    flightNumber: str
    flightDate: str
    scheduledDeparture: str
    scheduledArrival: str
    type: str
    rootCause: str | None = None
    status: str
    impact: dict[str, Any]
    passengerImpact: dict[str, Any]
    crewImpact: dict[str, Any]
    costEstimate: dict[str, Any] | None = None
    actionPlan: dict[str, Any] | None = None
    _audit: dict[str, Any]


class FlightQueueResponse(BaseModel):
    flights: list[FlightSummary]


class FlightManifestResponse(BaseModel):
    manifest: FlightManifest
    passengers: list[PassengerSummary]
    crew: list[CrewMember]
    disruption: FlightDisruption | None = None


class PassengerDetailResponse(BaseModel):
    passenger: PassengerDetail
    flight: FlightSummary | None = None
    options: list[ReaccommodationOption] = Field(default_factory=list)
    crew: list[CrewMember] = Field(default_factory=list)
