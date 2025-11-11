#!/usr/bin/env python3
"""Generate Cathay-aligned mock data, persist it to MongoDB, and stream it via Kafka."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import count
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Sequence

from dateutil import tz

try:  # Python 3.12+
  from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # Python <=3.11 fallback
  UTC = timezone.utc
from faker import Faker
from pymongo import MongoClient
from pymongo.collection import Collection
from pydantic import BaseModel, ConfigDict, Field

try:  # Kafka is optional during local dev
  from kafka import KafkaProducer
  from kafka.errors import KafkaError, NoBrokersAvailable
except ImportError:  # pragma: no cover - handled at runtime
  KafkaProducer = None  # type: ignore[assignment]
  KafkaError = Exception  # type: ignore[misc]
  NoBrokersAvailable = Exception  # type: ignore[misc]

HK_TZ = tz.gettz("Asia/Hong_Kong")
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "mock"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
  fake = Faker("en_HK")
except AttributeError:
  fake = Faker("en_US")
Faker.seed(42)
random.seed(42)

STATUS_LABELS: dict[str, dict[str, str]] = {
  "normal": {"label": "On track", "color": "#059669"},
  "warning": {"label": "Attention", "color": "#b45309"},
  "critical": {"label": "Critical", "color": "#b91c1c"},
}

TURN_MILESTONES = ["Crew inbound", "Turn clean", "Fuel", "Boarding", "Pushback"]

TierType = Literal["Green", "Silver", "Gold", "Diamond"]

AIRPORT_PROFILES: dict[str, dict[str, Any]] = {
  "HKG": {
    "icao": "VHHH",
    "name": "Hong Kong International",
    "city": "Hong Kong",
    "country": "HKG",
    "timezone": "Asia/Hong_Kong",
    "lat": 22.3089,
    "lon": 113.9146,
  },
  "LHR": {
    "icao": "EGLL",
    "name": "London Heathrow",
    "city": "London",
    "country": "GBR",
    "timezone": "Europe/London",
    "lat": 51.47,
    "lon": -0.4543,
  },
  "NRT": {
    "icao": "RJAA",
    "name": "Tokyo Narita",
    "city": "Narita",
    "country": "JPN",
    "timezone": "Asia/Tokyo",
    "lat": 35.7653,
    "lon": 140.3853,
  },
  "MNL": {
    "icao": "RPLL",
    "name": "Manila Ninoy Aquino",
    "city": "Manila",
    "country": "PHL",
    "timezone": "Asia/Manila",
    "lat": 14.5086,
    "lon": 121.0192,
  },
  "SFO": {
    "icao": "KSFO",
    "name": "San Francisco International",
    "city": "San Francisco",
    "country": "USA",
    "timezone": "America/Los_Angeles",
    "lat": 37.6213,
    "lon": -122.379,
  },
  "CDG": {
    "icao": "LFPG",
    "name": "Paris Charles de Gaulle",
    "city": "Paris",
    "country": "FRA",
    "timezone": "Europe/Paris",
    "lat": 49.0097,
    "lon": 2.5479,
  },
  "LAX": {
    "icao": "KLAX",
    "name": "Los Angeles International",
    "city": "Los Angeles",
    "country": "USA",
    "timezone": "America/Los_Angeles",
    "lat": 33.9416,
    "lon": -118.4085,
  },
  "SIN": {
    "icao": "WSSS",
    "name": "Singapore Changi",
    "city": "Singapore",
    "country": "SGP",
    "timezone": "Asia/Singapore",
    "lat": 1.3644,
    "lon": 103.9915,
  },
}

FLEET_CONFIG = {
  "A350-900": {
    "label": "Airbus A350-900",
    "count": 28,
    "config": {"business": 28, "premiumEconomy": 28, "economy": 256, "total": 312},
    "range": 15000,
    "fuel": 141000,
    "co2": 0.092,
    "wingspan": 64.75,
    "engines": "Trent XWB-84",
    "maint_cost": 2800,
    "length": 66.8,
  },
  "A350-1000": {
    "label": "Airbus A350-1000",
    "count": 18,
    "config": {"business": 32, "premiumEconomy": 24, "economy": 256, "total": 312},
    "range": 16100,
    "fuel": 156000,
    "co2": 0.087,
    "wingspan": 64.75,
    "engines": "Trent XWB-97",
    "maint_cost": 3100,
    "length": 73.8,
  },
  "A330-300": {
    "label": "Airbus A330-300",
    "count": 33,
    "config": {"business": 39, "premiumEconomy": 21, "economy": 191, "total": 251},
    "range": 11300,
    "fuel": 97500,
    "co2": 0.105,
    "wingspan": 60.3,
    "engines": "Trent 772B",
    "maint_cost": 2200,
    "length": 63.7,
  },
  "B777-300ER": {
    "label": "Boeing 777-300ER",
    "count": 53,
    "config": {"first": 6, "business": 53, "premiumEconomy": 34, "economy": 242, "total": 335},
    "range": 13649,
    "fuel": 171170,
    "co2": 0.098,
    "wingspan": 64.8,
    "engines": "GE90-115B",
    "maint_cost": 3500,
    "length": 73.9,
  },
  "B777-300": {
    "label": "Boeing 777-300",
    "count": 17,
    "config": {"business": 42, "premiumEconomy": 0, "economy": 304, "total": 346},
    "range": 11000,
    "fuel": 171170,
    "co2": 0.102,
    "wingspan": 60.9,
    "engines": "PW4090",
    "maint_cost": 3200,
    "length": 73.9,
  },
  "A321neo": {
    "label": "Airbus A321neo",
    "count": 12,
    "config": {"business": 12, "economy": 190, "total": 202},
    "range": 7400,
    "fuel": 23700,
    "co2": 0.078,
    "wingspan": 35.8,
    "engines": "LEAP-1A",
    "maint_cost": 1800,
    "length": 44.5,
  },
  "B747-8F": {
    "label": "Boeing 747-8F",
    "count": 14,
    "config": {"cargo": True, "total": 0},
    "range": 14815,
    "fuel": 238610,
    "co2": 0.0,
    "wingspan": 68.4,
    "engines": "GEnx-2B67",
    "maint_cost": 4200,
    "length": 76.3,
  },
}

REGISTRY_FORMAT = {
  "A350-900": {"prefix": "B-LR", "mode": "alpha"},
  "A350-1000": {"prefix": "B-LX", "mode": "alpha"},
  "A330-300": {"prefix": "B-LA", "mode": "alpha"},
  "B777-300ER": {"prefix": "B-KQ", "mode": "alpha"},
  "B777-300": {"prefix": "B-HN", "mode": "alpha"},
  "A321neo": {"prefix": "B-LP", "mode": "numeric"},
  "B747-8F": {"prefix": "B-LD", "mode": "numeric"},
}

AIRCRAFT_CODE_LOOKUP = {
  "A350-900": {"icao": "A359", "iata": "359"},
  "A350-1000": {"icao": "A35K", "iata": "351"},
  "A330-300": {"icao": "A333", "iata": "333"},
  "B777-300ER": {"icao": "B77W", "iata": "77W"},
  "B777-300": {"icao": "B773", "iata": "773"},
  "A321neo": {"icao": "A21N", "iata": "32Q"},
  "B747-8F": {"icao": "B748", "iata": "74N"},
}

CABIN_FIELD_TO_CODE = {
  "first": "F",
  "business": "J",
  "premiumEconomy": "W",
  "economy": "Y",
}

MAINTENANCE_EVENT_TYPES = ["A_CHECK", "C_CHECK", "UNSCHEDULED", "ENGINE_SWAP"]
MAINTENANCE_FINDINGS = [
  "Hydraulic line chafing",
  "Cabin pressure controller reset",
  "Left engine borescope",
  "GPU connector replacement",
  "Avionics cooling fan swapped",
]

CREW_ID_COUNTER = count(120000)
USED_PNRS: set[str] = set()
USED_BOOKINGS: set[str] = set()

FLIGHT_TEMPLATES = [
  {
    "flightNumber": "CX255",
    "route": "HKG → LHR",
    "destination": "London Heathrow",
    "aircraft": "Airbus A350-1000",
    "aircraftType": "A350-1000",
    "gate": "W22",
    "standbyGate": "W30",
    "blockMinutes": 780,
    "severity": "High",
  },
  {
    "flightNumber": "CX520",
    "route": "HKG → NRT",
    "destination": "Tokyo Narita",
    "aircraft": "Airbus A350-900",
    "aircraftType": "A350-900",
    "gate": "N65",
    "standbyGate": "N67",
    "blockMinutes": 245,
    "severity": "Medium",
  },
  {
    "flightNumber": "CX903",
    "route": "HKG → MNL",
    "destination": "Manila",
    "aircraft": "Airbus A321neo",
    "aircraftType": "A321neo",
    "gate": "E15",
    "standbyGate": "E17",
    "blockMinutes": 140,
    "severity": "Low",
  },
  {
    "flightNumber": "CX865",
    "route": "HKG → SFO",
    "destination": "San Francisco",
    "aircraft": "Boeing 777-300ER",
    "aircraftType": "B777-300ER",
    "gate": "N312",
    "standbyGate": "N510",
    "blockMinutes": 720,
    "severity": "Medium",
  },
  {
    "flightNumber": "CX315",
    "route": "HKG → CDG",
    "destination": "Paris Charles de Gaulle",
    "aircraft": "Airbus A350-900",
    "aircraftType": "A350-900",
    "gate": "W19",
    "standbyGate": "W21",
    "blockMinutes": 740,
    "severity": "High",
  },
  {
    "flightNumber": "CX872",
    "route": "HKG → LAX",
    "destination": "Los Angeles",
    "aircraft": "Boeing 777-300ER",
    "aircraftType": "B777-300ER",
    "gate": "N73",
    "standbyGate": "N75",
    "blockMinutes": 760,
    "severity": "Medium",
  },
  {
    "flightNumber": "CX708",
    "route": "HKG → SIN",
    "destination": "Singapore",
    "aircraft": "Airbus A330-300",
    "aircraftType": "A330-300",
    "gate": "S32",
    "standbyGate": "S34",
    "blockMinutes": 210,
    "severity": "Low",
  },
]

SSR_CODES = ["WCHR", "WCHC", "BLND", "DEAF", "VGML", "AVML", "CHLD", "INFT", "EXBG"]
TIER_WEIGHTS: dict[TierType, int] = {"Green": 40, "Silver": 30, "Gold": 20, "Diamond": 10}
WHY_REASON_TYPES = ["tier", "time", "policy", "risk", "revenue"]


def iso_format(dt: datetime) -> str:
  return dt.astimezone(UTC).isoformat()


def hk_now() -> datetime:
  return datetime.now(tz=HK_TZ)


def _alpha_suffix(index: int) -> str:
  first = index // 26
  second = index % 26
  return f"{chr(65 + first)}{chr(65 + second)}"


def _numeric_suffix(index: int) -> str:
  return f"{index + 1:02d}"


def build_registration(model: str, index: int) -> str:
  fmt = REGISTRY_FORMAT.get(model, {"prefix": "B-LN", "mode": "alpha"})
  suffix = _alpha_suffix(index) if fmt["mode"] == "alpha" else _numeric_suffix(index)
  return f"{fmt['prefix']}{suffix}"


def delay_profile(severity: str) -> tuple[int, int]:
  if severity == "High":
    return (40, 120)
  if severity == "Medium":
    return (10, 60)
  return (0, 20)


def derive_delay_minutes(severity: str) -> int:
  low, high = delay_profile(severity)
  if high == 0:
    return 0
  delay = random.randint(low, high)
  if severity == "Low" and random.random() < 0.45:
    return 0
  return delay


def status_category_from_delay(delay: int) -> Literal["normal", "warning", "critical"]:
  if delay >= 45:
    return "critical"
  if delay >= 15:
    return "warning"
  return "normal"


def turn_progress_percent(now: datetime, scheduled: datetime) -> float:
  prep_start = scheduled - timedelta(minutes=120)
  total = max((scheduled - prep_start).total_seconds(), 1)
  if now <= prep_start:
    return 5.0
  if now >= scheduled:
    return 99.0
  elapsed = (now - prep_start).total_seconds()
  progress = max(5.0, min(99.0, (elapsed / total) * 100))
  return round(progress, 1)


def milestone_states(progress: float) -> list[dict[str, str]]:
  milestones: list[dict[str, str]] = []
  for index, label in enumerate(TURN_MILESTONES):
    threshold = (index + 1) * (100 / len(TURN_MILESTONES))
    if progress >= threshold + 10:
      state = "complete"
    elif progress >= threshold - 10:
      state = "active"
    else:
      state = "pending"
    milestones.append({"label": label, "state": state})
  return milestones


def readiness_flags(progress: float) -> tuple[bool, bool, bool]:
  crew_ready = progress >= 25
  aircraft_ready = progress >= 55
  ground_ready = progress >= 45
  return crew_ready, aircraft_ready, ground_ready


def baggage_status_from_progress(progress: float) -> str:
  if progress >= 85:
    return "Closed"
  if progress >= 60:
    return "Loading"
  if progress >= 30:
    return "Staging"
  return "Queued"


def fuel_status_from_progress(progress: float) -> str:
  if progress >= 80:
    return "Complete"
  if progress >= 50:
    return "In progress"
  return "Queued"


def irregular_ops_payload(flight_number: str, status: Literal["normal", "warning", "critical"]) -> dict[str, Any]:
  action_bank = {
    "critical": [
      "Request slot swap with partner tail",
      "Alert premium services for reprotect",
      "Coordinate spare aircraft assignment",
    ],
    "warning": [
      "Ping crew control for readiness",
      "Stage vouchers in CX App",
      "Reconfirm fueling ETA",
    ],
    "normal": [
      "Monitor PRD weather build-up",
      "Keep four seats free for reprotect",
      "Share ETA with duty manager",
    ],
  }
  reasons = {
    "critical": "High impact disruption — evaluate swap options",
    "warning": "Operational hold — monitoring turnaround",
    "normal": "On schedule — continue monitoring",
  }
  actions = random.sample(action_bank[status], k=min(3, len(action_bank[status])))
  return {"reason": reasons[status], "actions": actions, "flight": flight_number}


def connection_snapshot(pax_count: int) -> dict[str, int]:
  tight = random.randint(4, min(24, max(6, pax_count // 8)))
  missed = random.randint(0, max(2, pax_count // 25))
  vip = random.randint(0, max(2, pax_count // 40))
  return {"tight": tight, "missed": missed, "vip": vip}


def _hash_ready_payload(payload: dict[str, Any]) -> dict[str, Any]:
  sanitized = json.loads(json.dumps(payload, default=str))
  metadata = sanitized.get("_metadata", {}).copy()
  metadata["hash"] = ""
  sanitized["_metadata"] = metadata
  return sanitized


def hash_object(payload: dict[str, Any]) -> str:
  sanitized = _hash_ready_payload(payload)
  return hashlib.sha256(json.dumps(sanitized, sort_keys=True).encode()).hexdigest()


def unique_code(factory: Callable[[], str], used: set[str]) -> str:
  for _ in range(20):
    candidate = factory()
    if candidate not in used:
      used.add(candidate)
      return candidate
  raise RuntimeError("Unable to generate unique code after 20 attempts")


def parse_route_codes(route: str) -> tuple[str, str]:
  parts = [segment.strip() for segment in route.split("→")]
  if len(parts) != 2:
    return ("HKG", parts[-1] if parts else "UNK")
  return parts[0], parts[1]


def cabin_weights_for_aircraft(aircraft: Aircraft) -> tuple[list[str], list[int]]:
  codes: list[str] = []
  weights: list[int] = []
  for field, code in CABIN_FIELD_TO_CODE.items():
    seats = aircraft.seating.get(field)
    if seats:
      codes.append(code)
      weights.append(int(seats))
  if not codes:
    total = aircraft.seating.get("total", 180)
    codes.append("Y")
    weights.append(int(total))
  return codes, weights


def pick_cabin(aircraft: Aircraft) -> str:
  codes, weights = cabin_weights_for_aircraft(aircraft)
  return random.choices(codes, weights=weights, k=1)[0]


def airport_profile(code: str) -> dict[str, Any]:
  profile = AIRPORT_PROFILES.get(code.upper())
  if profile:
    return {"iata": code.upper(), **profile}
  return {
    "iata": code.upper(),
    "icao": "",
    "name": code.upper(),
    "city": code.upper(),
    "country": "",
    "timezone": "UTC",
    "lat": 0.0,
    "lon": 0.0,
  }


def crew_ranks_for_flight(flight: dict[str, Any], aircraft: Aircraft) -> list[str]:
  seats = aircraft.seating.get("total") or aircraft.seating.get("economy", 200)
  base_size = 9 if seats <= 220 else 12 if seats <= 300 else 15
  augmented = 1 if flight["blockMinutes"] >= 600 else 0
  cockpit = 2 + augmented
  purser = 1
  lead_cabin = 1
  remaining = max(base_size - (cockpit + purser + lead_cabin), 3)
  ranks = ["CPT"] + ["FO"] * (cockpit - 1) + ["PUR"] + ["CC"] * lead_cabin + ["FA"] * remaining
  return ranks


def assignment_history(departure_time: datetime) -> list[dict[str, Any]]:
  history: list[dict[str, Any]] = []
  for _ in range(random.randint(1, 3)):
    completed = departure_time - timedelta(hours=random.randint(18, 96))
    history.append(
      {
        "flightNumber": f"CX{random.randint(100, 999)}",
        "completedAt": iso_format(completed),
        "dutyHours": round(random.uniform(6.5, 13.5), 1),
      }
    )
  return history


def maintenance_history(registration: str) -> list[MaintenanceEvent]:
  events: list[MaintenanceEvent] = []
  for idx in range(random.randint(1, 3)):
    completed = datetime.now(tz=UTC) - timedelta(days=random.randint(15, 420))
    due = completed + timedelta(days=random.randint(45, 320))
    status = random.choices(["CLEARED", "DEFERRED", "OPEN"], weights=[70, 20, 10])[0]
    events.append(
      MaintenanceEvent(
        eventId=f"MX-{registration}-{idx}",
        eventType=random.choice(MAINTENANCE_EVENT_TYPES),
        completedAt=iso_format(completed),
        dueAt=iso_format(due),
        findings=random.choice(MAINTENANCE_FINDINGS),
        status=status,
      )
    )
  return events


def max_takeoff_weight(model: str) -> int:
  if model.startswith("A350"):
    return 280000
  if model.startswith("A330"):
    return 242000
  if model.startswith("A321"):
    return 97500
  if model.startswith("B777"):
    return 351500
  if model.startswith("B747"):
    return 447700
  return 250000


def generate_aircraft_fleet() -> list[Aircraft]:
  fleet: list[Aircraft] = []
  counters: defaultdict[str, int] = defaultdict(int)
  now = datetime.now(tz=UTC)

  for model, spec in FLEET_CONFIG.items():
    for _ in range(spec["count"]):
      idx = counters[model]
      counters[model] += 1
      registration = build_registration(model, idx)
      delivery = fake.date_between(start_date="-15y", end_date="-2y")
      age_days = (now.date() - delivery).days
      age_years = max(age_days / 365.25, 0.5)
      hours = int(age_years * random.uniform(2800, 4200))
      cycles = int(hours * random.uniform(0.6, 0.85))
      code_pair = AIRCRAFT_CODE_LOOKUP.get(model, {"icao": model[:4], "iata": model[:3]})
      cabin_config = "/".join(
        [f"{count}{CABIN_FIELD_TO_CODE[field]}" for field, count in spec["config"].items() if field in CABIN_FIELD_TO_CODE]
      )
      status = random.choices(["ACTIVE", "MAINT", "AOG", "STORAGE"], weights=[88, 7, 3, 2])[0]
      last_a = now - timedelta(days=random.randint(20, 180))
      last_c = now - timedelta(days=random.randint(160, 980))
      compat = sorted({"HKG", "TPE", "LHR", "SFO", "CDG", "SIN", "NRT", "MNL", "LAX", "BKK"})
      maintenance_events = maintenance_history(registration)
      payload = {
        "registration": registration,
        "type": model,
        "icaoCode": code_pair["icao"],
        "iataCode": code_pair["iata"],
        "fleetNumber": f"{model}-{idx + 1:03d}",
        "deliveryDate": delivery.isoformat(),
        "ageYears": round(age_years, 1),
        "totalFlightHours": hours,
        "totalCycles": cycles,
        "seating": spec["config"],
        "cabinConfig": cabin_config,
        "rangeKm": spec["range"],
        "fuelCapacityLiters": spec["fuel"],
        "maxTakeoffWeightKg": max_takeoff_weight(model),
        "cruiseSpeedKmh": 900 if model.startswith("A350") else 890 if model.startswith("B777") else 840,
        "co2PerPaxKm": spec["co2"],
        "fuelBurnPerHourKg": int(spec["fuel"] * 0.045),
        "status": status,
        "lastACheck": iso_format(last_a),
        "lastCCheck": iso_format(last_c),
        "apuStatus": random.choice(["OK", "FAULT", "REPLACED"]),
        "engine1": {"type": spec["engines"], "hours": hours - random.randint(80, 900), "cycles": cycles - random.randint(40, 300)},
        "engine2": {"type": spec["engines"], "hours": hours - random.randint(80, 900), "cycles": cycles - random.randint(40, 300)},
        "wingspanM": spec["wingspan"],
        "lengthM": spec["length"],
        "requiresWideGate": spec["wingspan"] > 60,
        "compatibleAirports": compat,
        "maintenanceCostPerHourUSD": spec["maint_cost"],
        "depreciationPerYearUSD": 12_000_000 if model.startswith("A350") else 8_000_000,
        "maintenanceHistory": maintenance_events,
        "statusNotes": aircraft_status_note(status),
        "_metadata": {
          "lastUpdated": iso_format(now),
          "source": "FLEET_DB",
          "hash": "",
        },
      }
      payload["_metadata"]["hash"] = hash_object(payload)
      fleet.append(Aircraft(**payload))

  return fleet


def aircraft_status_note(status: str) -> str:
  notes = {
    "ACTIVE": "Released for departure bank",
    "MAINT": "In hangar for overnight check",
    "AOG": "Grounded pending engineering decision",
    "STORAGE": "Parked long term — swap required",
  }
  return notes.get(status.upper(), "Fleet update pending")


def aircraft_pool_by_type(fleet: list[Aircraft]) -> dict[str, list[Aircraft]]:
  pool: dict[str, list[Aircraft]] = defaultdict(list)
  for aircraft in fleet:
    pool[aircraft.type].append(aircraft)
  for aircraft_list in pool.values():
    random.shuffle(aircraft_list)
  return pool


def assign_aircraft(template: dict[str, Any], pool: dict[str, list[Aircraft]]) -> Aircraft:
  model = template.get("aircraftType") or template.get("aircraft") or "A350-900"
  candidates = pool.get(model)
  if not candidates:
    # fallback to any available aircraft
    fallback_list = random.choice(list(pool.values()))
    candidates = fallback_list
  aircraft = candidates.pop(0)
  candidates.append(aircraft)
  pool[model] = candidates
  return aircraft


class MaintenanceEvent(BaseModel):
  model_config = ConfigDict(frozen=True)

  eventId: str
  eventType: Literal["A_CHECK", "C_CHECK", "UNSCHEDULED", "ENGINE_SWAP"]
  completedAt: str
  dueAt: str
  findings: str
  status: Literal["CLEARED", "DEFERRED", "OPEN"]


class Aircraft(BaseModel):
  model_config = ConfigDict(frozen=True)

  registration: str
  type: str
  icaoCode: str
  iataCode: str
  fleetNumber: str
  deliveryDate: str
  ageYears: float
  totalFlightHours: int
  totalCycles: int
  seating: dict[str, Any]
  cabinConfig: str
  rangeKm: int
  fuelCapacityLiters: int
  maxTakeoffWeightKg: int
  cruiseSpeedKmh: int
  co2PerPaxKm: float
  fuelBurnPerHourKg: float
  status: Literal["ACTIVE", "MAINT", "AOG", "STORAGE"]
  lastACheck: str | None = None
  lastCCheck: str | None = None
  apuStatus: Literal["OK", "FAULT", "REPLACED"]
  engine1: dict[str, Any]
  engine2: dict[str, Any]
  wingspanM: float
  lengthM: float
  requiresWideGate: bool
  compatibleAirports: list[str]
  maintenanceCostPerHourUSD: int
  depreciationPerYearUSD: int
  maintenanceHistory: list[MaintenanceEvent]
  statusNotes: str
  _metadata: dict[str, Any]


class WhyReason(BaseModel):
  model_config = ConfigDict(frozen=True)

  text: str
  type: str


class ReaccommodationOption(BaseModel):
  model_config = ConfigDict(frozen=True)

  id: str
  departureTime: str
  arrivalTime: str
  route: str
  cabin: str
  seats: int
  trvScore: int
  arrivalDelta: str | None = None
  badges: list[str] = Field(default_factory=list)
  whyReasons: list[WhyReason]


class TierBreakdown(BaseModel):
  model_config = ConfigDict(frozen=True)

  tier: TierType
  count: int


class CabinBreakdown(BaseModel):
  model_config = ConfigDict(frozen=True)

  cabin: str
  count: int


class CohortPassenger(BaseModel):
  model_config = ConfigDict(frozen=True)

  pnr: str
  name: str
  tier: TierType
  defaultOption: str
  confidence: int
  hasException: bool
  notes: str | None = None
  cabin: str


class FlightSummary(BaseModel):
  model_config = ConfigDict(frozen=True)

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
  model_config = ConfigDict(frozen=True)

  flightNumber: str
  summary: FlightSummary
  passengerIds: list[str]
  crewIds: list[str]
  options: list[ReaccommodationOption]
  cohortPassengers: list[CohortPassenger]
  disruptionId: str


class Crew(BaseModel):
  model_config = ConfigDict(frozen=True)

  employeeId: str
  firstName: str
  lastName: str
  rank: str
  base: str
  currentLocation: str
  qualifications: dict[str, Any]
  duty: dict[str, Any]
  assignment: dict[str, Any] | None
  availability: dict[str, Any]
  contact: dict[str, Any]
  assignmentHistory: list[dict[str, Any]] = Field(default_factory=list)
  fatigueRisk: Literal["low", "medium", "high"]
  currentDutyPhase: str
  readinessState: Literal["ready", "standby", "hold"]
  statusNote: str
  commsPreference: str
  _metadata: dict[str, Any]
  flightNumber: str


class Passenger(BaseModel):
  model_config = ConfigDict(frozen=True)

  pnr: str
  bookingReference: str
  basePassenger: dict[str, Any]
  cathayProfile: dict[str, Any]
  disruptionContext: dict[str, Any]
  metadata: dict[str, Any]
  revenueValue: int
  cabin: str
  ssrs: list[str]
  contact: str
  originalFlight: str
  originalRoute: str
  originalTime: str
  isPRM: bool
  hasInfant: bool
  hasFamily: bool


class FlightDisruption(BaseModel):
  model_config = ConfigDict(frozen=True)

  disruptionId: str
  flightNumber: str
  flightDate: str
  scheduledDeparture: str
  scheduledArrival: str
  type: str
  rootCause: str | None
  status: str
  impact: dict[str, Any]
  passengerImpact: dict[str, Any]
  crewImpact: dict[str, Any]
  costEstimate: dict[str, Any] | None = None
  actionPlan: dict[str, Any] | None = None
  _audit: dict[str, Any]


class FlightRecord(BaseModel):
  model_config = ConfigDict(frozen=True)

  flightNumber: str
  departureAirport: dict[str, Any]
  arrivalAirport: dict[str, Any]
  departureTime: str
  arrivalTime: str
  scheduledDeparture: str
  scheduledArrival: str
  estimatedDeparture: str
  estimatedArrival: str
  blockMinutes: int
  severity: Literal["High", "Medium", "Low"]
  status: str
  statusCategory: Literal["normal", "warning", "critical"]
  statusColor: str
  delayMinutes: int
  loadFactor: float
  passengerCount: int
  premiumPax: int
  aircraft: dict[str, Any]
  crewAssignments: list[dict[str, Any]]
  passengerIds: list[str]
  disruptionId: str
  gate: str
  standbyGate: str
  fuelPlanKg: int
  maintenanceStatus: str
  statusText: str
  paxImpacted: int
  connections: dict[str, int]
  turnProgress: float
  crewReady: bool
  aircraftReady: bool
  groundReady: bool
  irregularOps: dict[str, Any]
  milestones: list[dict[str, str]]
  baggageStatus: str
  fuelStatus: str
  lastUpdated: str
  tailNumber: str
  timezone: str


@dataclass(slots=True)
class DatasetBundle:
  manifests: list[FlightManifest]
  passengers: list[Passenger]
  crew: list[Crew]
  disruptions: list[FlightDisruption]
  aircraft: list[Aircraft]
  flights: list[FlightRecord]


@dataclass(slots=True)
class MongoConfig:
  uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
  db_name: str = os.getenv("MONGO_DB_NAME", "runwayops")
  manifest_collection: str = os.getenv("MONGO_FLIGHT_COLLECTION", "flight_manifests")
  passenger_collection: str = os.getenv("MONGO_PASSENGER_COLLECTION", "passengers")
  crew_collection: str = os.getenv("MONGO_CREW_COLLECTION", "crew")
  disruption_collection: str = os.getenv("MONGO_DISRUPTION_COLLECTION", "disruptions")
  aircraft_collection: str = os.getenv("MONGO_AIRCRAFT_COLLECTION", "aircraft")
  flight_instance_collection: str = os.getenv("MONGO_FLIGHT_INSTANCE_COLLECTION", "flight_instances")


@dataclass(slots=True)
class KafkaConfig:
  enabled: bool = os.getenv("KAFKA_ENABLED", "true").lower() not in {"0", "false"}
  bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
  flight_topic: str = os.getenv("KAFKA_FLIGHT_TOPIC", "flight-manifests")
  passenger_topic: str = os.getenv("KAFKA_PASSENGER_TOPIC", "passenger-events")
  crew_topic: str = os.getenv("KAFKA_CREW_TOPIC", "crew-events")


def generate_passenger(flight: dict[str, Any], departure_time: datetime, aircraft: Aircraft) -> Passenger:
  tier = random.choices(list(TIER_WEIGHTS.keys()), weights=TIER_WEIGHTS.values())[0]
  cabin = pick_cabin(aircraft)
  ssrs = list({random.choice(SSR_CODES) for _ in range(random.randint(0, 2)) if random.random() < 0.5})
  has_infant = "INFT" in ssrs
  has_family = random.random() < 0.25
  is_prm = any(code.startswith("WCH") for code in ssrs)
  booking_class = {"F": "F", "J": "J", "W": "E", "Y": "Y"}[cabin]
  passenger_name = fake.name()
  pnr = unique_code(lambda: fake.bothify("??###?").upper(), USED_PNRS)
  booking_reference = unique_code(lambda: f"CX-{random.randint(100000, 999999)}", USED_BOOKINGS)

  base_data = {
    "personalDetails": {
      "title": random.choice(["Mr", "Ms", "Mrs", "Mx"]),
      "firstName": passenger_name.split()[0],
      "lastName": passenger_name.split()[-1],
      "dateOfBirth": fake.date_of_birth(minimum_age=18, maximum_age=78).isoformat(),
      "gender": random.choice(["M", "F", "X"]),
      "nationality": random.choice(["HKG", "USA", "GBR", "CAN", "AUS"]),
      "passportNumber": fake.bothify(text="??#######").upper(),
      "passportExpiry": fake.date_between(start_date="+2y", end_date="+8y").isoformat(),
      "specialAssistance": {
        "wheelchair": is_prm,
        "mealPreference": random.choice(["VGML", "AVML", "SFML", None]),
      },
    },
    "contactInfo": {
      "email": fake.email(),
      "phone": fake.phone_number(),
      "address": {
        "street": fake.street_address(),
        "city": fake.city(),
        "postalCode": fake.postcode(),
        "country": random.choice(["HK", "US", "GB", "AU", "CA"]),
      },
    },
    "travelDetails": {
      "bookingClass": booking_class,
      "ticketNumber": f"125-{random.randint(1000000000, 9999999999)}",
      "frequentFlyerNumber": f"MPC{random.randint(100000000, 999999999)}",
      "ssr": ssrs,
      "preferences": {
        "seatPreference": random.choice(["Window", "Aisle"]),
        "language": random.choice(["en-US", "zh-HK", "fr-FR"]),
        "communicationChannel": random.choice(["App", "Email", "SMS"]),
      },
    },
  }

  loyalty = {
    "programName": "Cathay Membership Programme",
    "memberId": base_data["travelDetails"]["frequentFlyerNumber"],
    "tier": tier,
    "statusPoints": random.randint(100, 1500),
    "pointsRollover": random.randint(0, 200),
    "membershipYear": str(datetime.now().year),
    "enrollmentDate": fake.date_between(start_date="-10y", end_date="-1y").isoformat(),
    "expirationDate": fake.date_between(start_date="+1y", end_date="+3y").isoformat(),
  }

  return Passenger(
    pnr=pnr,
    bookingReference=booking_reference,
    basePassenger=base_data,
    cathayProfile={
      "loyaltyProgram": loyalty,
      "rewardsBalance": {
        "asiaMiles": random.randint(5_000, 120_000),
        "clubPoints": random.randint(100, 2_000),
      },
      "benefitsEligibility": {
        "priorityCheckIn": tier in {"Gold", "Diamond"},
        "loungeAccess": tier in {"Gold", "Diamond"},
        "extraBaggage": 32 if tier in {"Gold", "Diamond"} else 23,
        "priorityRebooking": tier != "Green",
        "guaranteedEconomySeat": tier in {"Gold", "Diamond"},
      },
      "travelHistory": {
        "lifetimeFlights": random.randint(20, 400),
        "segmentsThisYear": random.randint(4, 60),
        "totalStatusPointsEarned": random.randint(1_000, 10_000),
      },
      "profilePreferences": {
        "sustainabilityOptIn": random.random() < 0.2,
        "notificationPreferences": random.sample(["Push", "Email", "SMS"], k=2),
        "familyTravel": has_family,
        "corporate": random.random() < 0.15,
      },
    },
    disruptionContext={
      "affectedFlight": flight["flightNumber"],
      "pnrPassengers": random.randint(1, 4),
      "connectionRisk": random.choice(["Low", "Medium", "High"]),
    },
    metadata={
      "lastUpdated": iso_format(datetime.now(tz=UTC)),
      "dataSource": "Altea PSS",
      "version": "1.0",
    },
    revenueValue=random.randint(500, 18000),
    cabin=cabin,
    ssrs=ssrs,
    contact=base_data["contactInfo"]["phone"],
    originalFlight=flight["flightNumber"],
    originalRoute=flight["route"],
    originalTime=departure_time.astimezone(HK_TZ).strftime("%H:%M"),
    isPRM=is_prm,
    hasInfant=has_infant,
    hasFamily=has_family,
  )


def generate_crew_for_flight(flight: dict[str, Any], departure_time: datetime, aircraft: Aircraft) -> list[Crew]:
  crew_members: list[Crew] = []
  ranks = crew_ranks_for_flight(flight, aircraft)
  origin_code, dest_code = parse_route_codes(flight["route"])
  report_time = departure_time - timedelta(hours=2)
  off_duty = departure_time + timedelta(minutes=flight["blockMinutes"] + 180)
  duty_phases = ["Report", "Briefing", "Boarding", "Standby", "Rest"]
  comms_channels = ["Ops chat", "Signal", "Phone call", "Sat phone"]
  status_messages = [
    "Crew brief complete",
    "Awaiting MX clearance",
    "Cabin secure checks underway",
    "Covering standby pool",
    "Resting post duty",
  ]

  for rank in ranks:
    employee_id = f"CX{next(CREW_ID_COUNTER)}"
    assignment_status = "ON_DUTY" if rank in {"CPT", "FO", "PUR"} else random.choice(["ON_DUTY", "STANDBY"])
    assignment = {
      "flightNumber": flight["flightNumber"],
      "leg": random.choice(["OUT", "RTN", "POS"]),
      "scheduledReport": iso_format(report_time),
      "estimatedOffDuty": iso_format(off_duty),
      "status": assignment_status,
      "aircraftRegistration": aircraft.registration,
      "aircraftType": aircraft.type,
    }
    fdp_remaining = round(random.uniform(3, 14), 1)
    fatigue_risk = "high" if fdp_remaining < 4 else "medium" if fdp_remaining < 7 else "low"
    duty_phase = random.choice(duty_phases)
    flight_status = flight.get("statusCategory", "normal")
    readiness_state = "ready"
    if flight_status == "critical":
      readiness_state = "hold"
    elif flight_status == "warning" and assignment_status != "ON_DUTY":
      readiness_state = "standby"

    status_note = random.choice(status_messages)
    comms_preference = random.choice(comms_channels)

    crew_members.append(
      Crew(
        employeeId=employee_id,
        firstName=fake.first_name(),
        lastName=fake.last_name(),
        rank=rank,
        base=origin_code,
        currentLocation=random.choice([origin_code, dest_code, "HKG"]),
        qualifications={
          "aircraftTypes": sorted({aircraft.type.split("-")[0], aircraft.type}),
          "languages": random.sample(["en", "zh", "ja", "fr", "yue"], k=2),
          "medicalExpiry": fake.date_between("+1y", "+3y").isoformat(),
          "recurrentTrainingDue": fake.date_between("+3m", "+1y").isoformat(),
        },
        duty={
          "fdpRemainingHours": fdp_remaining,
          "flightTime28d": random.randint(48, 98),
          "requiredRestHours": random.choice([10, 12, 14]),
        },
        assignment=assignment,
        availability={
          "earliestAvailable": iso_format(off_duty + timedelta(hours=random.randint(6, 12))),
          "maxDutyExtensionHours": random.choice([0, 1, 2]),
        },
        contact={
          "phone": fake.phone_number(),
          "email": f"{fake.user_name()}@cathay.com".lower(),
        },
        assignmentHistory=assignment_history(departure_time),
        fatigueRisk=fatigue_risk,
        currentDutyPhase=duty_phase,
        readinessState=readiness_state,
        statusNote=status_note,
        commsPreference=comms_preference,
        _metadata={
          "version": random.randint(1, 3),
          "lastUpdated": iso_format(datetime.now(tz=UTC)),
          "source": random.choice(["CREW_ROSTER", "OPS"]),
          "changeLogId": f"log-crew-{uuid.uuid4()}",
        },
        flightNumber=flight["flightNumber"],
      )
    )
  return crew_members


def generate_disruption(
  flight: dict[str, Any],
  departure_time: datetime,
  passenger_count: int,
  crew: list[Crew],
  aircraft: Aircraft,
) -> FlightDisruption:
  disruption_id = f"DIS-{departure_time.strftime('%Y%m%d')}-{flight['flightNumber']}"
  delay_minutes = random.randint(10, 180)
  status = random.choice(["PREDICTED", "ACTIVE"])
  crew_unavailable = random.sample([c.employeeId for c in crew], k=random.randint(0, min(3, len(crew))))
  cause_pool = ["ATC slot restriction", "Crew legality", "Weather en-route", "Ground handling delay"]
  if aircraft.status != "ACTIVE":
    cause_pool.append("Maintenance release hold")

  return FlightDisruption(
    disruptionId=disruption_id,
    flightNumber=flight["flightNumber"],
    flightDate=departure_time.date().isoformat(),
    scheduledDeparture=iso_format(departure_time),
    scheduledArrival=iso_format(departure_time + timedelta(minutes=flight["blockMinutes"])),
    type=random.choice(["DELAY", "CREW", "WEATHER", "ATC"]),
    rootCause=random.choice(cause_pool),
    status=status,
    impact={
      "delayMinutes": delay_minutes,
      "newDeparture": iso_format(departure_time + timedelta(minutes=delay_minutes)),
      "cancelled": False,
    },
    passengerImpact={
      "totalPax": passenger_count,
      "connectingPax": int(passenger_count * random.uniform(0.2, 0.4)),
      "highValuePax": int(passenger_count * random.uniform(0.05, 0.12)),
      "protectedPax": int(passenger_count * random.uniform(0.1, 0.2)),
    },
    crewImpact={
      "requiredCrew": len(crew),
      "unavailableCrew": crew_unavailable,
      "standbyCrewAvailable": random.randint(0, 5),
    },
    costEstimate={
      "compensationEUR261": random.randint(5_000, 30_000),
      "hotelNights": random.randint(0, passenger_count // 3),
      "mealVouchers": passenger_count,
      "rebookingCost": random.randint(8_000, 50_000),
      "totalUSD": random.randint(20_000, 120_000),
    },
    actionPlan={
      "rebookedFlight": random.choice(["CX882", "CX900", "CX251"]),
      "hotelBookingId": f"HTL-{random.randint(10000, 99999)}",
      "crewSwap": crew_unavailable,
      "approvedBy": random.choice(["OPS-001", "OPS-002", "OPS-003"]),
      "approvedAt": iso_format(datetime.now(tz=UTC)),
      "confidence": round(random.uniform(0.7, 0.98), 2),
      "aircraftSwapCandidate": aircraft.registration if random.random() < 0.35 else None,
    },
    _audit={
      "createdAt": iso_format(datetime.now(tz=UTC)),
      "createdBy": random.choice(["PREDICTIVE_MODEL", "OPS_STAFF"]),
      "updates": [],
      "finalHash": uuid.uuid4().hex,
    },
  )


def generate_options(flight: dict[str, Any], departure_time: datetime) -> list[ReaccommodationOption]:
  options: list[ReaccommodationOption] = []
  for idx in range(3):
    base_departure = departure_time + timedelta(hours=idx * 4 - 2)
    arrival = base_departure + timedelta(minutes=flight["blockMinutes"])
    arrival_local = arrival.astimezone(HK_TZ)
    departure_local = base_departure.astimezone(HK_TZ)
    day_delta = (arrival_local.date() - departure_local.date()).days
    arrival_suffix = f"+{day_delta}" if day_delta else ""
    option_id = chr(ord("A") + idx)
    reasons = [
      WhyReason(text="Priority tier auto-protected", type="tier"),
      WhyReason(text="Keeps arrival within 2h window", type="time"),
      WhyReason(text="Maintains premium revenue", type="revenue"),
      WhyReason(text="SSR requirements honored", type="policy"),
      WhyReason(text="Reduces knock-on risk", type="risk"),
    ]
    options.append(
      ReaccommodationOption(
        id=option_id,
        departureTime=departure_local.strftime("%H:%M"),
        arrivalTime=f"{arrival_local.strftime('%H:%M')}{arrival_suffix}",
        route=flight["route"],
        cabin=random.choice(["J", "W", "Y"]),
        seats=random.randint(5, 40),
        trvScore=random.randint(65, 98),
        arrivalDelta=random.choice(["+2h earlier", "+4h later", "+1h earlier"]),
        badges=random.sample(["Protected", "Fastest", "Greener"], k=random.randint(0, 2)),
        whyReasons=random.sample(reasons, k=random.randint(3, len(reasons))),
      )
    )
  return options


def summarise_flight(
  template: dict[str, Any],
  passengers: Sequence[Passenger],
  crew: Sequence[Crew],
  options: Sequence[ReaccommodationOption],
  departure_time: datetime,
) -> FlightManifest:
  tier_counts = Counter(p.cathayProfile["loyaltyProgram"]["tier"] for p in passengers)
  cabin_counts = Counter(p.cabin for p in passengers)
  exceptions = sum(1 for p in passengers if p.isPRM or p.hasInfant)

  summary = FlightSummary(
    flightNumber=template["flightNumber"],
    route=template["route"],
    destination=template["destination"],
    severity=template["severity"],
    affectedCount=len(passengers),
    tierBreakdown=[
      TierBreakdown(tier=tier, count=count) for tier, count in sorted(tier_counts.items())
    ],
    cabinBreakdown=[
      CabinBreakdown(cabin=cabin, count=count) for cabin, count in sorted(cabin_counts.items())
    ],
    defaultSuitability=random.randint(70, 96),
    exceptions=exceptions,
    blockMinutes=template["blockMinutes"],
    aircraft=template["aircraft"],
    statusText=random.choice(
      [
        "Crew legality risk",
        "Awaiting ATC slot",
        "MX release pending",
        "Weather reroute in effect",
      ]
    ),
    updatedAt=iso_format(datetime.now(tz=UTC)),
  )

  cohort_passengers: list[CohortPassenger] = []
  for passenger in random.sample(list(passengers), k=min(10, len(passengers))):
    notes = None
    if passenger.isPRM:
      notes = "PRM"
    elif passenger.hasInfant:
      notes = "Infant"
    elif passenger.hasFamily:
      notes = "Family"

    cohort_passengers.append(
      CohortPassenger(
        pnr=passenger.pnr,
        name=f"{passenger.basePassenger['personalDetails']['firstName']} {passenger.basePassenger['personalDetails']['lastName']}",
        tier=passenger.cathayProfile["loyaltyProgram"]["tier"],
        defaultOption=options[0].id,
        confidence=random.randint(70, 98),
        hasException=notes is not None,
        notes=notes,
        cabin=passenger.cabin,
      )
    )

  disruption_id = f"DIS-{departure_time.strftime('%Y%m%d')}-{template['flightNumber']}"

  return FlightManifest(
    flightNumber=template["flightNumber"],
    summary=summary,
    passengerIds=[p.pnr for p in passengers],
    crewIds=[c.employeeId for c in crew],
    options=list(options),
    cohortPassengers=cohort_passengers,
    disruptionId=disruption_id,
  )


def build_flight_record(
  template: dict[str, Any],
  departure_time: datetime,
  passengers: Sequence[Passenger],
  crew: Sequence[Crew],
  manifest: FlightManifest,
  aircraft: Aircraft,
) -> FlightRecord:
  origin_code, dest_code = parse_route_codes(template["route"])
  departure_airport = airport_profile(origin_code)
  arrival_airport = airport_profile(dest_code)
  arrival_time = departure_time + timedelta(minutes=template["blockMinutes"])
  capacity = aircraft.seating.get("total", len(passengers)) or len(passengers)
  passenger_count = len(passengers)
  load_factor = round(min(passenger_count / capacity, 1.0), 2)
  maintenance_flags = [event.findings for event in aircraft.maintenanceHistory if event.status != "CLEARED"]
  crew_assignments = [
    {
      "employeeId": member.employeeId,
      "rank": member.rank,
      "status": (member.assignment or {}).get("status", "ON_DUTY"),
    }
    for member in crew
  ]
  scheduled_departure = iso_format(departure_time)
  scheduled_arrival = iso_format(arrival_time)
  delay_minutes = derive_delay_minutes(template["severity"])
  estimated_departure_dt = departure_time + timedelta(minutes=delay_minutes)
  estimated_arrival_dt = arrival_time + timedelta(minutes=delay_minutes)
  estimated_departure = iso_format(estimated_departure_dt)
  estimated_arrival = iso_format(estimated_arrival_dt)
  status_category = status_category_from_delay(delay_minutes)
  now_reference = hk_now()
  turn_progress = turn_progress_percent(now_reference, departure_time)
  crew_ready, aircraft_ready, ground_ready = readiness_flags(turn_progress)
  connections = connection_snapshot(passenger_count)
  pax_impacted = int(passenger_count * (0.3 if status_category != "normal" else 0.08))
  premium_pax = max(8, int(passenger_count * random.uniform(0.18, 0.28)))
  irregular_ops = irregular_ops_payload(template["flightNumber"], status_category)
  milestones = milestone_states(turn_progress)
  baggage_status = baggage_status_from_progress(turn_progress)
  fuel_status = fuel_status_from_progress(turn_progress)
  last_updated = iso_format(datetime.now(tz=UTC))
  aircraft_snapshot = {
    "registration": aircraft.registration,
    "type": aircraft.type,
    "tail": aircraft.registration,
    "status": aircraft.status,
    "lastACheck": aircraft.lastACheck,
    "lastCCheck": aircraft.lastCCheck,
    "apuStatus": aircraft.apuStatus,
    "maintenanceFlags": maintenance_flags,
  }

  fuel_plan = int((template["blockMinutes"] / 60 + 1.2) * aircraft.fuelBurnPerHourKg)
  maintenance_status = "OPEN_FINDINGS" if maintenance_flags else aircraft.status
  status_text = manifest.summary.statusText
  status_color = STATUS_LABELS[status_category]["color"]
  timezone_label = departure_airport.get("timezone", "Asia/Hong_Kong")

  return FlightRecord(
    flightNumber=template["flightNumber"],
    departureAirport=departure_airport,
    arrivalAirport=arrival_airport,
    departureTime=scheduled_departure,
    arrivalTime=scheduled_arrival,
    scheduledDeparture=scheduled_departure,
    scheduledArrival=scheduled_arrival,
    estimatedDeparture=estimated_departure,
    estimatedArrival=estimated_arrival,
    blockMinutes=template["blockMinutes"],
    severity=template["severity"],
    status=status_text,
    statusCategory=status_category,
    statusColor=status_color,
    delayMinutes=delay_minutes,
    loadFactor=load_factor,
    passengerCount=passenger_count,
    premiumPax=premium_pax,
    aircraft=aircraft_snapshot,
    crewAssignments=crew_assignments,
    passengerIds=[p.pnr for p in passengers],
    disruptionId=manifest.disruptionId or "",
    gate=template.get("gate", "TBD"),
    standbyGate=template.get("standbyGate", ""),
    fuelPlanKg=fuel_plan,
    maintenanceStatus=maintenance_status,
    statusText=status_text,
    paxImpacted=pax_impacted,
    connections=connections,
    turnProgress=turn_progress,
    crewReady=crew_ready,
    aircraftReady=aircraft_ready,
    groundReady=ground_ready,
    irregularOps=irregular_ops,
    milestones=milestones,
    baggageStatus=baggage_status,
    fuelStatus=fuel_status,
    lastUpdated=last_updated,
    tailNumber=aircraft.registration,
    timezone=timezone_label,
  )


def build_dataset(multiplier: int, base_passenger_count: int) -> DatasetBundle:
  manifests: list[FlightManifest] = []
  passengers: list[Passenger] = []
  crew_members: list[Crew] = []
  disruptions: list[FlightDisruption] = []
  flight_records: list[FlightRecord] = []

  fleet = generate_aircraft_fleet()
  aircraft_assignments = aircraft_pool_by_type(fleet)

  templates = []
  while len(templates) < multiplier:
    templates.extend(FLIGHT_TEMPLATES)
  templates = templates[:multiplier]

  for template in templates:
    departure_time = hk_now() + timedelta(minutes=random.randint(20, 240))
    aircraft = assign_aircraft(template, aircraft_assignments)
    capacity = aircraft.seating.get("total") or base_passenger_count
    capacity = capacity if capacity and capacity > 0 else base_passenger_count
    passenger_count = max(
      60,
      int(capacity * random.uniform(0.65, 0.97)),
    )
    pax = [generate_passenger(template, departure_time, aircraft) for _ in range(passenger_count)]
    crew = generate_crew_for_flight(template, departure_time, aircraft)
    options = generate_options(template, departure_time)
    manifest = summarise_flight(template, pax, crew, options, departure_time)
    disruption = generate_disruption(template, departure_time, len(pax), crew, aircraft)
    record = build_flight_record(template, departure_time, pax, crew, manifest, aircraft)

    passengers.extend(pax)
    crew_members.extend(crew)
    manifests.append(manifest)
    disruptions.append(disruption)
    flight_records.append(record)

  return DatasetBundle(
    manifests=manifests,
    passengers=passengers,
    crew=crew_members,
    disruptions=disruptions,
    aircraft=fleet,
    flights=flight_records,
  )


def write_json_fixtures(bundle: DatasetBundle) -> None:
  def _dump(path: Path, payload: Iterable[BaseModel]) -> None:
    path.write_text(
      json.dumps([item.model_dump(mode="json") for item in payload], indent=2, ensure_ascii=False),
      encoding="utf-8",
    )

  _dump(OUTPUT_DIR / "crew.json", bundle.crew)
  _dump(OUTPUT_DIR / "passengers.json", bundle.passengers)
  _dump(OUTPUT_DIR / "disruptions.json", bundle.disruptions)
  _dump(OUTPUT_DIR / "aircraft.json", bundle.aircraft)
  (OUTPUT_DIR / "flight_manifests.json").write_text(
    json.dumps([m.model_dump(mode="json") for m in bundle.manifests], indent=2, ensure_ascii=False),
    encoding="utf-8",
  )
  (OUTPUT_DIR / "flight_records.json").write_text(
    json.dumps([f.model_dump(mode="json") for f in bundle.flights], indent=2, ensure_ascii=False),
    encoding="utf-8",
  )


def persist_to_mongo(bundle: DatasetBundle, config: MongoConfig) -> None:
  client = MongoClient(config.uri)
  db = client[config.db_name]

  def _replace(collection: Collection, docs: Iterable[BaseModel]) -> None:
    collection.delete_many({})
    payload = [doc.model_dump(mode="json") for doc in docs]
    if payload:
      collection.insert_many(payload)

  _replace(db[config.manifest_collection], bundle.manifests)
  _replace(db[config.passenger_collection], bundle.passengers)
  _replace(db[config.crew_collection], bundle.crew)
  _replace(db[config.disruption_collection], bundle.disruptions)
  _replace(db[config.aircraft_collection], bundle.aircraft)
  _replace(db[config.flight_instance_collection], bundle.flights)
  client.close()
  print(
    f"Persisted {len(bundle.manifests)} manifests, {len(bundle.passengers)} passengers, "
    f"{len(bundle.crew)} crew, {len(bundle.disruptions)} disruptions, {len(bundle.aircraft)} aircraft"
    f" and {len(bundle.flights)} flight records to MongoDB ({config.db_name})."
  )


def stream_to_kafka(bundle: DatasetBundle, config: KafkaConfig) -> None:
  if not config.enabled:
    print("Kafka streaming disabled via KAFKA_ENABLED.")
    return
  if KafkaProducer is None:
    print("kafka-python not installed; skipping Kafka streaming.")
    return
  try:
    producer = KafkaProducer(
      bootstrap_servers=config.bootstrap_servers,
      value_serializer=lambda value: json.dumps(value).encode("utf-8"),
      key_serializer=lambda value: value.encode("utf-8") if value else None,
    )
  except NoBrokersAvailable as exc:  # type: ignore[call-arg]
    print(f"Kafka broker unavailable ({exc}); skipping streaming.")
    return

  def _send(topic: str, key: str, payload: BaseModel) -> None:
    producer.send(topic, key=key, value=payload.model_dump(mode="json"))

  for manifest in bundle.manifests:
    _send(config.flight_topic, manifest.flightNumber, manifest)

  for passenger in bundle.passengers:
    _send(config.passenger_topic, passenger.pnr, passenger)

  for crew in bundle.crew:
    _send(config.crew_topic, crew.employeeId, crew)

  try:
    producer.flush(timeout=10)
    print(
      f"Streamed {len(bundle.manifests)} flight events, {len(bundle.passengers)} passenger events, "
      f"{len(bundle.crew)} crew events to Kafka."
    )
  except KafkaError as exc:  # type: ignore[call-arg]
    print(f"Kafka flush failed: {exc}")
  finally:
    producer.close()


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Generate Cathay mock data and persist it to Mongo/Kafka.")
  parser.add_argument("--flights", type=int, default=len(FLIGHT_TEMPLATES), help="Number of flight manifests to create.")
  parser.add_argument("--base-passengers", type=int, default=180, help="Average passenger count per flight.")
  parser.add_argument("--no-json", action="store_true", help="Skip writing JSON fixture files.")
  parser.add_argument("--no-mongo", action="store_true", help="Skip MongoDB persistence.")
  parser.add_argument("--no-kafka", action="store_true", help="Skip Kafka streaming.")
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  bundle = build_dataset(multiplier=args.flights, base_passenger_count=args.base_passengers)
  if not args.no_json:
    write_json_fixtures(bundle)
  if not args.no_mongo:
    persist_to_mongo(bundle, MongoConfig())
  if not args.no_kafka:
    stream_to_kafka(bundle, KafkaConfig())


if __name__ == "__main__":
  main()
