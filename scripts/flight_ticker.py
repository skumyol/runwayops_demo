#!/usr/bin/env python3
"""Continuously perturb Mongo flight instances to mimic a realtime ticker."""

from __future__ import annotations

import argparse
import os
import random
import time
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Optional

from dateutil import tz
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError

HK_TZ = tz.gettz("Asia/Hong_Kong")

STATUS_LABELS: dict[str, dict[str, str]] = {
    "normal": {"label": "On track", "color": "#059669"},
    "warning": {"label": "Attention", "color": "#b45309"},
    "critical": {"label": "Critical", "color": "#b91c1c"},
}

CREW_PHASES = ["Report", "Briefing", "Boarding", "Standby", "Rest"]
CREW_NOTES = [
    "Brief complete",
    "Awaiting MX release",
    "Cabin prep in progress",
    "Covering standby pool",
    "On rest break",
]
CREW_CHANNELS = ["Ops chat", "Signal", "Phone call", "Sat phone"]


def aircraft_status_note(status: str) -> str:
    notes = {
        "ACTIVE": "Released for departure bank",
        "MAINT": "Hangar inspection underway",
        "AOG": "Grounded pending engineering decision",
        "STORAGE": "Parked long term — swap required",
    }
    return notes.get(status.upper(), "Fleet update pending")


def iso_format(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def status_category(delay: int) -> str:
    if delay >= 45:
        return "critical"
    if delay >= 15:
        return "warning"
    return "normal"


def turn_progress(now: datetime, scheduled: datetime) -> float:
    prep_start = scheduled - timedelta(minutes=120)
    total = max((scheduled - prep_start).total_seconds(), 1)
    if now <= prep_start:
        return 5.0
    if now >= scheduled:
        return 99.0
    elapsed = (now - prep_start).total_seconds()
    return round(max(5.0, min(99.0, (elapsed / total) * 100)), 1)


def readiness_flags(progress: float) -> tuple[bool, bool, bool]:
    return progress >= 25, progress >= 55, progress >= 45


def baggage_status(progress: float) -> str:
    if progress >= 85:
        return "Closed"
    if progress >= 60:
        return "Loading"
    if progress >= 30:
        return "Staging"
    return "Queued"


def fuel_status(progress: float) -> str:
    if progress >= 80:
        return "Complete"
    if progress >= 50:
        return "In progress"
    return "Queued"


def jitter_for_severity(severity: str) -> int:
    table = {
        "High": (-5, 12),
        "Medium": (-3, 8),
        "Low": (-2, 4),
    }
    low, high = table.get(severity, (-2, 4))
    return random.randint(low, high)


def update_connections(snapshot: dict[str, int]) -> dict[str, int]:
    next_snapshot = snapshot.copy()
    for key in ("tight", "missed", "vip"):
        baseline = next_snapshot.get(key, 0)
        drift = random.randint(-2, 2 if key == "tight" else 1)
        next_snapshot[key] = max(0, baseline + drift)
    return next_snapshot


def compute_updates(doc: dict[str, Any], now: datetime) -> dict[str, Any]:
    scheduled = parse_iso(doc.get("scheduledDeparture") or doc.get("departureTime"))
    scheduled_arrival = parse_iso(doc.get("scheduledArrival") or doc.get("arrivalTime"))
    if not scheduled or not scheduled_arrival:
        return {}

    delay = int(doc.get("delayMinutes", 0))
    severity = doc.get("severity", "Low")
    delay_delta = jitter_for_severity(severity)
    new_delay = max(0, min(240, delay + delay_delta))
    new_status_category = status_category(new_delay)

    est_departure = scheduled + timedelta(minutes=new_delay)
    est_arrival = scheduled_arrival + timedelta(minutes=new_delay)
    progress = turn_progress(now, scheduled)
    crew_ready, aircraft_ready, ground_ready = readiness_flags(progress)
    pax_count = int(doc.get("passengerCount", 180))
    pax_impacted = int(pax_count * (0.32 if new_status_category != "normal" else 0.08))
    connections = update_connections(doc.get("connections", {}))

    status_message = doc.get("status") or doc.get("statusText") or "Operational update"
    if new_status_category == "normal":
        status_message = "On track"
    elif delay_delta >= 0:
        status_message = f"Delay {new_delay} min — monitoring"
    else:
        status_message = f"Delay improving ({new_delay} min)"

    return {
        "delayMinutes": new_delay,
        "estimatedDeparture": iso_format(est_departure),
        "estimatedArrival": iso_format(est_arrival),
        "statusCategory": new_status_category,
        "statusColor": STATUS_LABELS[new_status_category]["color"],
        "status": status_message,
        "turnProgress": progress,
        "crewReady": crew_ready,
        "aircraftReady": aircraft_ready,
        "groundReady": ground_ready,
        "paxImpacted": pax_impacted,
        "connections": connections,
        "baggageStatus": baggage_status(progress),
        "fuelStatus": fuel_status(progress),
        "lastUpdated": iso_format(now),
    }


def run_ticker(
    collection: Collection,
    iterations: int,
    sleep_seconds: int,
    crew_collection: Optional[Collection] = None,
    aircraft_collection: Optional[Collection] = None,
    update_crew: bool = False,
    update_aircraft: bool = False,
) -> None:
    loop = 0
    while iterations == 0 or loop < iterations:
        now = datetime.now(tz=HK_TZ)
        docs = list(collection.find({}, {"_id": 1, "severity": 1, "delayMinutes": 1, "scheduledDeparture": 1,
                                         "scheduledArrival": 1, "departureTime": 1, "arrivalTime": 1,
                                         "statusCategory": 1, "statusColor": 1, "turnProgress": 1,
                                         "crewReady": 1, "aircraftReady": 1, "groundReady": 1,
                                         "passengerCount": 1, "connections": 1}))
        if not docs:
            print("No flight instances found. Exiting ticker.")
            return

        updated = 0
        for doc in docs:
            updates = compute_updates(doc, now)
            if updates:
                collection.update_one({"_id": doc["_id"]}, {"$set": updates})
                updated += 1

        crew_updates = (
            update_crew_snapshots(
                crew_collection,
                {doc.get("flightNumber"): doc.get("statusCategory", "normal") for doc in docs if doc.get("flightNumber")},
                now,
            )
            if update_crew and crew_collection
            else 0
        )
        aircraft_updates = (
            update_aircraft_snapshots(
                aircraft_collection,
                {doc.get("tailNumber"): doc.get("statusCategory", "normal") for doc in docs if doc.get("tailNumber")},
                now,
            )
            if update_aircraft and aircraft_collection
            else 0
        )

        print(
            f"[{iso_format(now)}] Updated {updated} flights | {crew_updates} crew | {aircraft_updates} aircraft"
        )
        loop += 1
        if iterations and loop >= iterations:
            break
        time.sleep(sleep_seconds)


def update_crew_snapshots(
    collection: Optional[Collection],
    flight_statuses: dict[str, str],
    now: datetime,
) -> int:
    if not collection or not flight_statuses:
        return 0
    crew_docs = list(
        collection.find(
            {"flightNumber": {"$in": list(flight_statuses.keys())}},
            {
                "_id": 1,
                "flightNumber": 1,
                "assignment": 1,
                "duty": 1,
                "currentDutyPhase": 1,
                "availability": 1,
                "readinessState": 1,
            },
        )
    )
    updated = 0
    for doc in crew_docs:
        duty = doc.get("duty") or {}
        current_fdp = float(duty.get("fdpRemainingHours", 8.0))
        new_fdp = max(1.0, current_fdp - random.uniform(0.2, 0.9))
        fatigue = (
            "high" if new_fdp < 4 else "medium" if new_fdp < 7 else "low"
        )
        current_phase = doc.get("currentDutyPhase") or random.choice(CREW_PHASES)
        try:
            phase_index = CREW_PHASES.index(current_phase)
        except ValueError:
            phase_index = random.randint(0, len(CREW_PHASES) - 1)
        next_phase = CREW_PHASES[(phase_index + 1) % len(CREW_PHASES)]
        flight_number = doc.get("flightNumber")
        severity = flight_statuses.get(flight_number, "normal")
        assignment = doc.get("assignment") or {}
        readiness = doc.get("readinessState", "ready")
        if severity == "critical":
            readiness = "hold"
        elif severity == "warning" and assignment.get("status") != "ON_DUTY":
            readiness = "standby"
        elif severity == "normal" and assignment.get("status") == "ON_DUTY":
            readiness = "ready"

        updates: dict[str, Any] = {
            "currentDutyPhase": next_phase,
            "fatigueRisk": fatigue,
            "readinessState": readiness,
            "statusNote": random.choice(CREW_NOTES),
            "commsPreference": random.choice(CREW_CHANNELS),
            "duty.fdpRemainingHours": round(new_fdp, 1),
            "_metadata.lastUpdated": iso_format(now),
        }
        availability = doc.get("availability") or {}
        earliest = availability.get("earliestAvailable")
        if earliest:
            base_dt = parse_iso(earliest) or now
            updates["availability.earliestAvailable"] = iso_format(
                base_dt + timedelta(minutes=random.randint(-15, 45))
            )
        collection.update_one({"_id": doc["_id"]}, {"$set": updates})
        updated += 1
    return updated


def update_aircraft_snapshots(
    collection: Optional[Collection],
    tail_statuses: dict[str, str],
    now: datetime,
) -> int:
    if not collection or not tail_statuses:
        return 0
    fleet_docs = list(
        collection.find(
            {"registration": {"$in": list(tail_statuses.keys())}},
            {"_id": 1, "registration": 1, "status": 1},
        )
    )
    updated = 0
    for doc in fleet_docs:
        tail = doc.get("registration")
        if not tail:
            continue
        severity = tail_statuses.get(tail, "normal")
        current_status = doc.get("status", "ACTIVE")
        next_status = drift_aircraft_status(current_status, severity)
        updates = {
            "status": next_status,
            "statusNotes": aircraft_status_note(next_status),
            "_metadata.lastUpdated": iso_format(now),
        }
        collection.update_one({"_id": doc["_id"]}, {"$set": updates})
        updated += 1
    return updated


def drift_aircraft_status(status: str, severity: str) -> str:
    normalized = (status or "ACTIVE").upper()
    if severity == "critical":
        return "AOG"
    if severity == "warning" and normalized == "ACTIVE" and random.random() < 0.3:
        return "MAINT"
    if severity == "normal" and normalized != "ACTIVE" and random.random() < 0.2:
        return "ACTIVE"
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply ticker-style updates to Mongo flight instances."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Number of update loops to run (0 = run forever).",
    )
    parser.add_argument(
        "--sleep",
        type=int,
        default=30,
        help="Seconds to sleep between update loops.",
    )
    parser.add_argument(
        "--mongo-uri",
        default=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        help="Mongo connection string.",
    )
    parser.add_argument(
        "--db-name",
        default=os.getenv("MONGO_DB_NAME", "runwayops"),
        help="Mongo database name.",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("MONGO_FLIGHT_INSTANCE_COLLECTION", "flight_instances"),
        help="Collection storing flight instance documents.",
    )
    parser.add_argument(
        "--crew-collection",
        default=os.getenv("MONGO_CREW_COLLECTION", "crew"),
        help="Collection storing crew roster documents.",
    )
    parser.add_argument(
        "--aircraft-collection",
        default=os.getenv("MONGO_AIRCRAFT_COLLECTION", "aircraft"),
        help="Collection storing aircraft documents.",
    )
    parser.add_argument(
        "--update-crew",
        action="store_true",
        help="Propagate ticker updates to crew readiness state.",
    )
    parser.add_argument(
        "--update-aircraft",
        action="store_true",
        help="Propagate ticker updates to aircraft readiness state.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = MongoClient(args.mongo_uri, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        raise SystemExit(f"Unable to reach MongoDB at {args.mongo_uri}: {exc}") from exc

    collection = client[args.db_name][args.collection]
    crew_collection = (
        client[args.db_name][args.crew_collection] if args.update_crew else None
    )
    aircraft_collection = (
        client[args.db_name][args.aircraft_collection] if args.update_aircraft else None
    )
    try:
        run_ticker(
            collection,
            iterations=args.iterations,
            sleep_seconds=args.sleep,
            crew_collection=crew_collection,
            aircraft_collection=aircraft_collection,
            update_crew=args.update_crew,
            update_aircraft=args.update_aircraft,
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
