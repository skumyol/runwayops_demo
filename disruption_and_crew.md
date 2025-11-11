Below is a **complete, production-ready data model** for **crew** and **flight-disruption** records that fits perfectly into the Cathay-Pacific hackathon prototype you are building.

* It is **IATA-compatible** (so it can be mapped to Amadeus Altea / SITA Crew-Manager).  
* It contains **all fields the LLM agents need** (Risk, Rebooking, Finance, Crew).  
* It is **immutable-by-design** – every change is appended to a black-box log.  
* It is **TypeScript-ready** (interfaces + JSON examples) and can be used directly in your React dashboard, FastAPI backend, and LangGraph agents.

---

## 1. Crew Object (one crew member)

```ts
interface Crew {
  /** Unique employee ID – same as in crew-roster system */
  employeeId: string;

  /** Full name */
  firstName: string;
  lastName: string;

  /** Rank / Position (IATA codes) */
  rank: 'CPT' | 'FO' | 'CC' | 'FA' | 'PUR' | string;   // CPT=Captain, FO=First Officer, CC=Chief Cabin, FA=Flight Attendant, PUR=Pursuer

  /** Base airport (home domicile) */
  base: string;               // e.g. "HKG"

  /** Current location (airport or city) – updated in real-time */
  currentLocation: string;

  /** Qualification & legal limits */
  qualifications: {
    aircraftTypes: string[];   // e.g. ["A350","B777"]
    languages: string[];       // e.g. ["en","zh"]
    medicalExpiry: string;     // ISO date
    recurrentTrainingDue: string;
  };

  /** Duty-time limits (ICAO / HKCAD) */
  duty: {
    /** Flight Duty Period – rolling 14-day limit */
    fdpRemainingHours: number;      // hours left in current FDP
    /** Cumulative flight time – 28-day limit */
    flightTime28d: number;          // hours
    /** Rest required before next duty */
    requiredRestHours: number;
  };

  /** Current assignment (if any) */
  assignment?: {
    flightNumber: string;           // e.g. "CX880"
    leg: 'OUT' | 'RTN' | 'POS';     // OUT=outbound, RTN=return, POS=positioning
    scheduledReport: string;        // ISO datetime
    estimatedOffDuty: string;
    status: 'ON_DUTY' | 'STANDBY' | 'REST' | 'OFF';
  };

  /** Availability for re-rostering */
  availability: {
    earliestAvailable: string;      // ISO datetime
    maxDutyExtensionHours: number; // how many extra hours the crew can accept
  };

  /** Contact */
  contact: {
    phone: string;
    email: string;
  };

  /** Metadata for black-box */
  _metadata: {
    version: number;
    lastUpdated: string;   // ISO
    source: 'CREW_ROSTER' | 'MOBILE_APP' | 'OPS';
    changeLogId: string;   // pointer to immutable log entry
  };
}
```

### Example JSON (Captain on standby)

```json
{
  "employeeId": "CX123456",
  "firstName": "Alice",
  "lastName": "Wong",
  "rank": "CPT",
  "base": "HKG",
  "currentLocation": "HKG",
  "qualifications": {
    "aircraftTypes": ["A350","B777"],
    "languages": ["en","zh"],
    "medicalExpiry": "2026-03-01",
    "recurrentTrainingDue": "2025-12-15"
  },
  "duty": {
    "fdpRemainingHours": 9.5,
    "flightTime28d": 78,
    "requiredRestHours": 12
  },
  "assignment": {
    "flightNumber": "CX880",
    "leg": "OUT",
    "scheduledReport": "2025-11-09T04:00:00Z",
    "estimatedOffDuty": "2025-11-09T14:30:00Z",
    "status": "STANDBY"
  },
  "availability": {
    "earliestAvailable": "2025-11-09T18:00:00Z",
    "maxDutyExtensionHours": 2
  },
  "contact": {
    "phone": "+852-9123-4567",
    "email": "alice.wong@cathay.com"
  },
  "_metadata": {
    "version": 2,
    "lastUpdated": "2025-11-08T15:42:11Z",
    "source": "CREW_ROSTER",
    "changeLogId": "log-987654321"
  }
}
```

---

## 2. Flight-Disruption Event (one IROP)

```ts
interface FlightDisruption {
  /** Unique disruption identifier */
  disruptionId: string;

  /** Affected flight */
  flightNumber: string;               // e.g. "CX880"
  flightDate: string;                 // ISO date of the operating day
  scheduledDeparture: string;         // ISO datetime (original STD)
  scheduledArrival: string;           // ISO datetime (original STA)

  /** Disruption classification */
  type: 'DELAY' | 'CANCEL' | 'DIVERT' | 'AOG' | 'CREW' | 'WEATHER' | 'ATC';
  rootCause?: string;                 // free-text or code

  /** Current status */
  status: 'PREDICTED' | 'ACTIVE' | 'RESOLVED' | 'CANCELLED';

  /** Predicted / actual impact */
  impact: {
    delayMinutes?: number;            // for DELAY
    newDeparture?: string;            // for re-scheduled
    newArrival?: string;
    diversionAirport?: string;        // for DIVERT
    cancelled: boolean;
  };

  /** Passenger impact (aggregated) */
  passengerImpact: {
    totalPax: number;
    connectingPax: number;
    highValuePax: number;             // Gold/Diamond
    protectedPax: number;             // EU261 / HKCAD protected
  };

  /** Crew impact */
  crewImpact: {
    requiredCrew: number;             // positions needed
    unavailableCrew: string[];        // employeeIds
    standbyCrewAvailable: number;
  };

  /** Cost estimate (Finance Agent output) */
  costEstimate?: {
    compensationEUR261?: number;
    hotelNights?: number;
    mealVouchers?: number;
    rebookingCost?: number;
    totalUSD?: number;
  };

  /** Action plan generated by LLM orchestrator */
  actionPlan?: {
    rebookedFlight?: string;
    hotelBookingId?: string;
    crewSwap?: string[];              // employeeIds
    approvedBy?: string;              // ops staff ID
    approvedAt?: string;
    confidence: number;               // 0-1 from Risk Agent
  };

  /** Immutable audit trail */
  _audit: {
    createdAt: string;
    createdBy: 'PREDICTIVE_MODEL' | 'OPS_STAFF' | 'ORCHESTRATOR';
    updates: Array<{
      timestamp: string;
      field: string;
      oldValue: any;
      newValue: any;
      actor: string;
    }>;
    finalHash: string;                // SHA-256 of the whole object
  };
}
```

### Example JSON (Delay → Re-scheduled)

```json
{
  "disruptionId": "DIS-20251108-CX880-01",
  "flightNumber": "CX880",
  "flightDate": "2025-11-08",
  "scheduledDeparture": "2025-11-08T22:00:00Z",
  "scheduledArrival": "2025-11-09T06:30:00Z",
  "type": "DELAY",
  "rootCause": "ATC slot restriction",
  "status": "ACTIVE",
  "impact": {
    "delayMinutes": 185,
    "newDeparture": "2025-11-09T01:05:00Z",
    "newArrival": "2025-11-09T09:35:00Z",
    "cancelled": false
  },
  "passengerImpact": {
    "totalPax": 312,
    "connectingPax": 87,
    "highValuePax": 24,
    "protectedPax": 41
  },
  "crewImpact": {
    "requiredCrew": 14,
    "unavailableCrew": ["CX123456","CX789012"],
    "standbyCrewAvailable": 3
  },
  "costEstimate": {
    "compensationEUR261": 12400,
    "hotelNights": 41,
    "mealVouchers": 312,
    "rebookingCost": 8500,
    "totalUSD": 32000
  },
  "actionPlan": {
    "rebookedFlight": "CX882",
    "hotelBookingId": "HTL-98765",
    "crewSwap": ["CX555111","CX555222"],
    "approvedBy": "OPS-001",
    "approvedAt": "2025-11-08T16:20:00Z",
    "confidence": 0.94
  },
  "_audit": {
    "createdAt": "2025-11-08T14:12:05Z",
    "createdBy": "PREDICTIVE_MODEL",
    "updates": [
      {
        "timestamp": "2025-11-08T16:18:11Z",
        "field": "actionPlan.approvedBy",
        "oldValue": null,
        "newValue": "OPS-001",
        "actor": "ops-dashboard"
      }
    ],
    "finalHash": "a1b2c3d4..."
  }
}
```

---

## 3. How to Store / Log Immutably (Black-Box)

```ts
// Append-only collection in MongoDB / PostgreSQL
interface DisruptionLog {
  logId: string;
  disruptionId: string;
  timestamp: string;
  payload: FlightDisruption;   // full snapshot at that moment
  hash: string;                // SHA-256 of JSON.stringify(payload)
  previousHash?: string;       // forms a chain
}
```

*Every change* (model prediction, ops approval, crew swap) creates a **new log entry** with a hash chain → tamper-proof audit for regulators and post-event analysis.

---

## 4. Quick Integration Checklist for Your Prototype

| Component | Field(s) used | Agent that consumes |
|-----------|---------------|---------------------|
| **Predictive Signal Generator** | `flightNumber`, `scheduledDeparture`, weather API | → creates `FlightDisruption` (status=PREDICTED) |
| **Risk Agent** | `impact.delayMinutes`, `passengerImpact.protectedPax` | → `actionPlan.confidence` |
| **Rebooking Agent** | `passengerImpact.highValuePax`, `cathayProfile.tier` | → chooses premium re-protection |
| **Finance Agent** | `costEstimate.*` | → fills `totalUSD` |
| **Crew Agent** | `crewImpact.unavailableCrew`, `Crew.availability` | → proposes `actionPlan.crewSwap` |
| **Ops Dashboard** | All fields + `_audit` | Approve → new log entry |
| **Passenger App** | `actionPlan.rebookedFlight`, `costEstimate.hotelNights` | Voice-chat explanation |

---

### TL;DR – Copy-Paste Ready

```ts
// src/types/index.ts
export * from './Crew';
export * from './FlightDisruption';
```

```ts
// src/types/Crew.ts
export interface Crew { … }   // paste the interface above
```

```ts
// src/types/FlightDisruption.ts
export interface FlightDisruption { … }   // paste the interface above
```

Now you have **complete, Cathay-aligned data contracts** that power every LLM sub-agent, the ops dashboard, the passenger voice-chat, and the immutable black-box. Plug them into your existing React + FastAPI + LangGraph stack and you’re ready for the hackathon demo!