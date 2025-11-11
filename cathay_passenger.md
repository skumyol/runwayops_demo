### Passenger Object Structure for Cathay Flight Disruption System

Based on standard airline passenger records (e.g., IATA PSS standards used in Cathay's Amadeus Altea system) and Cathay Pacific's updated loyalty program (as of November 2025), I've designed a comprehensive **Passenger Object** in JSON format. This combines:

- **Base Passenger Data**: Core details from booking/PNR (Passenger Name Record), including demographics, contact, and travel info for personalization in disruptions (e.g., rebooking with hotels).
- **Cathay Profile**: Integration with the **Cathay Membership Programme** (formerly Marco Polo Club + Asia Miles, revamped in October 2025 for simpler progression and benefits). Tiers are Green (entry), Silver (300 Status Points), Gold (600), Diamond (1,200); benefits include priority rebooking, lounge access, and miles redemption. Membership year is calendar-based from 2026, with rollover points for easier tier progression.

This structure is extensible for your LLM system (e.g., Risk Agent uses tier for priority; Rebooking Agent personalizes based on miles/preferences). Use it in TypeScript/JSON for your React dashboard or agent payloads.

#### Example JSON Passenger Object
```json
{
  "pnr": "ABC123456",
  "bookingReference": "CX-789012",
  "basePassenger": {
    "personalDetails": {
      "title": "Mr",
      "firstName": "John",
      "lastName": "Doe",
      "middleName": "A",
      "dateOfBirth": "1985-05-15",
      "gender": "M",
      "nationality": "USA",
      "passportNumber": "123456789",
      "passportExpiry": "2030-12-31",
      "specialAssistance": {
        "wheelchair": false,
        "mealPreference": "VGML"  // Vegan meal (IATA code)
      }
    },
    "contactInfo": {
      "email": "john.doe@email.com",
      "phone": "+1-555-123-4567",
      "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postalCode": "10001",
        "country": "USA"
      }
    },
    "travelDetails": {
      "bookingClass": "J",  // Business (Cathay fare class)
      "ticketNumber": "125-1234567890",
      "frequentFlyerNumber": "MPC123456789",  // Marco Polo Club ID
      "ssr": ["YUPG", "EXBG"],  // Special Service Requests (e.g., young passenger, extra baggage)
      "preferences": {
        "seatPreference": "Window",
        "language": "en-US",
        "communicationChannel": "App"  // App, Email, SMS
      }
    }
  },
  "cathayProfile": {
    "loyaltyProgram": {
      "programName": "Cathay Membership Programme",  // Updated from Marco Polo Club
      "memberId": "MPC123456789",
      "tier": "Gold",  // Green, Silver, Gold, Diamond
      "statusPoints": 650,  // Earned in current year (thresholds: Silver=300, Gold=600, Diamond=1,200)
      "pointsRollover": 50,  // New 2025 feature for easier progression
      "membershipYear": "2025",  // Calendar year from 2026
      "enrollmentDate": "2020-01-15",
      "expirationDate": "2026-12-31"
    },
    "rewardsBalance": {
      "asiaMiles": 45000,  // Redeemable for upgrades/hotels
      "clubPoints": 1200  // For lounge access/redemptions
    },
    "benefitsEligibility": {
      "priorityCheckIn": true,
      "loungeAccess": true,  // Cathay lounges + oneworld partners
      "extraBaggage": 32,  // Kg allowance (tier-based)
      "priorityRebooking": true,  // Gold+ get upgrades/miles for disruptions
      "guaranteedEconomySeat": true  // Gold+ benefit
    },
    "travelHistory": {
      "lifetimeFlights": 150,
      "segmentsThisYear": 25,
      "totalStatusPointsEarned": 8500
    },
    "profilePreferences": {
      "sustainabilityOptIn": true,  // For green rebooking options
      "notificationPreferences": ["Push", "Email"],
      "familyTravel": false,  // For child-related disruptions
      "corporate": false  // For business traveler perks
    }
  },
  "disruptionContext": {
    "affectedFlight": "CX880",
    "pnrPassengers": 1,  // Number in PNR
    "connectionRisk": "Low"  // Pre-calculated for multi-leg
  },
  "metadata": {
    "lastUpdated": "2025-11-08T14:30:00Z",
    "dataSource": "Altea PSS",  // For your blackbox logging
    "version": "1.0"
  }
}
```

#### Key Design Notes
- **Base Passenger**: Draws from IATA/OSI/SSR codes (e.g., meal prefs, special assistance) for global compatibility. Essential for rebooking (e.g., hotels via profile).
- **Cathay Profile**: Reflects 2025 updates—simpler tiers, rollover points, combined Asia Miles + status. Tier determines disruption perks (e.g., Diamond gets priority lounge/hotels).
- **Extensibility**: Add fields like `disruptionHistory` for your agents. Use for LLM prompts (e.g., "Prioritize Gold member with 45k miles").
- **Privacy**: Anonymize sensitive data (e.g., hash passport) for prototypes; comply with GDPR in production.
- **Usage in Your System**: Feed to Orchestrator for simulations (e.g., Rebooking Agent checks tier for upgrades). In dashboard, display tier for ops approvals.

This object is ready for your React/TS dashboard (e.g., as PropTypes) or agent payloads. If you need a schema validator (e.g., Zod) or mock generator, let me know!