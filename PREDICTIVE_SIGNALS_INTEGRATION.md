# Predictive Signals Integration

## Overview
This document describes the integration of predictive signals into the IROP (Irregular Operations) system. Predictive signals now automatically update flight disruption data and are displayed through flight card alerts.

## Implementation Summary

### Backend Changes

#### 1. Disruption Updater Service (`backend/app/services/disruption_updater.py`)
- **Purpose**: Periodically computes and stores predictive signals, enhancing flight data with AI-driven insights
- **Key Features**:
  - Computes risk probability based on weather, crew, and aircraft signals
  - Generates flight-specific predictive alerts with recommendations
  - Enriches disrupted flights with `predictiveAlert` field
  - Maintains latest signals for quick retrieval

#### 2. Synthetic Provider Integration (`backend/app/providers/synthetic.py`)
- **Enhancement**: Automatically calls `DisruptionUpdater` on every payload generation
- **Effect**: Flight data now includes predictive alerts when disruptions are detected

#### 3. New API Endpoint (`backend/app/main.py`)
- **Endpoint**: `GET /api/predictive-alerts/{flight_number}`
- **Query Parameters**: `airport`, `carrier`, `mode`
- **Response**:
  ```json
  {
    "flightNumber": "CX520",
    "hasPredictiveAlert": true,
    "alert": {
      "riskProbability": 0.92,
      "severity": "high",
      "drivers": [
        {
          "category": "Weather",
          "score": 0.31,
          "evidence": "Multiple weather alerts"
        }
      ],
      "recommendations": [
        "Monitor weather conditions: Multiple weather alerts",
        "Consider pre-emptive slot adjustments"
      ],
      "timestamp": "2025-11-14T03:10:04Z"
    },
    "flightStatus": {
      "statusCategory": "critical",
      "status": "Gate hold (ATC flow)",
      "delayMinutes": 34,
      "paxImpacted": 96
    }
  }
  ```

### Frontend Changes

#### 1. Predictive Alerts Hook (`frontend/dashboard/src/hooks/usePredictiveAlerts.ts`)
- **Purpose**: Fetches predictive alert data for specific flights
- **Exports**: `usePredictiveAlerts()` hook with `loading`, `error`, `alertData`, `fetchAlerts()`

#### 2. Enhanced Flight Alerts Modal (`frontend/dashboard/src/views/RealtimeFlightMonitor.tsx`)
- **Location**: `FlightAlertsModal` component
- **Features**:
  - Automatically fetches predictive signals when modal opens
  - Displays risk probability with visual progress bar
  - Shows risk drivers (Weather, Crew, Aircraft) with scores
  - Lists AI-generated recommendations
  - Includes operational actions from flight data
  - Loading state with animation
  - Timestamp of signal generation

## User Experience

### Flight Dashboard
- **No Changes**: Predictive signals are NOT shown on the main flight dashboard view
- **Rationale**: Keeps the dashboard clean and focused on operational status

### Flight Card Notifications
- **Trigger**: Click the alert triangle icon (⚠️) on any disrupted flight card
- **Action**: Opens modal with predictive signals

### Flight Detail View
- **Trigger**: Click "View alerts" button on flight detail page
- **Action**: Opens same modal with predictive signals

### Modal Content
The alert modal now displays three sections:
1. **Operational Status**: Current flight status and impact
2. **Predictive Signals** (if available):
   - Risk severity badge (LOW/MEDIUM/HIGH)
   - Disruption probability percentage
   - Risk driver breakdown with evidence
   - AI recommendations
3. **Operational Actions**: Standard IROP actions

## How It Works

1. **Data Generation**: Every time `/api/flight-monitor` is called, the synthetic provider:
   - Generates base flight data
   - Calls `DisruptionUpdater.compute_and_store_signals()`
   - Enhances disrupted flights with `predictiveAlert` field

2. **Signal Computation**: The updater:
   - Analyzes weather keywords in alerts
   - Evaluates crew readiness and fatigue
   - Checks aircraft status
   - Calculates weighted risk probability
   - Generates flight-specific recommendations

3. **Frontend Display**: When a user clicks alert icons:
   - Modal opens and calls `fetchAlerts(flightNumber)`
   - Backend returns flight's `predictiveAlert` data
   - UI renders risk drivers, probability, and recommendations
   - Auto-refreshes based on timestamp

## Testing

### Backend Test
```bash
# Test the flight monitor endpoint
curl "http://localhost:8000/api/flight-monitor?airport=HKG&carrier=CX&mode=synthetic" | python3 -m json.tool

# Test predictive alerts for a specific flight
curl "http://localhost:8000/api/predictive-alerts/CX520?airport=HKG&carrier=CX&mode=synthetic" | python3 -m json.tool
```

### Expected Results
- Disrupted flights (critical/warning status) should have `predictiveAlert` field
- Risk probability should be between 0.0 and 1.0
- Recommendations should be relevant to detected drivers
- On-time flights may not have specific alerts

### Frontend Test
1. Start the development server: `./run_dev.sh`
2. Open http://localhost:3000
3. Navigate to Realtime Flight Monitor
4. Click the alert triangle (⚠️) on any disrupted flight (e.g., CX520, CX315)
5. Verify the modal shows:
   - Operational status section
   - Predictive signals section with risk probability
   - Risk drivers with evidence
   - AI recommendations
   - Timestamp

## Configuration

### Backend
- **Update Interval**: 30 seconds (configurable in `DisruptionUpdater.__init__`)
- **Risk Thresholds**: 
  - High: ≥ 0.7
  - Medium: ≥ 0.5
  - Low: < 0.5

### Frontend
- **API Base**: Configured via `VITE_MONITOR_API` environment variable
- **Default**: `http://localhost:8000`

## Future Enhancements

Potential improvements:
1. **Real-time Updates**: WebSocket integration for live signal updates
2. **Historical Trends**: Show signal history over time
3. **Alert Thresholds**: User-configurable risk thresholds
4. **Action Tracking**: Log which recommendations were followed
5. **ML Model Integration**: Replace heuristic scoring with trained models
6. **Multi-airport**: Extend signals across multiple stations

## Files Modified/Created

### Backend
- ✨ **NEW**: `backend/app/services/disruption_updater.py`
- 📝 **MODIFIED**: `backend/app/providers/synthetic.py`
- 📝 **MODIFIED**: `backend/app/main.py`

### Frontend
- ✨ **NEW**: `frontend/dashboard/src/hooks/usePredictiveAlerts.ts`
- 📝 **MODIFIED**: `frontend/dashboard/src/views/RealtimeFlightMonitor.tsx`

## Notes

- Predictive signals update automatically with each payload refresh (every 30 seconds)
- The system works with synthetic data; real-time mode would follow the same pattern
- Alert recommendations are generated based on risk drivers and flight context
- The modal is reusable across different views (monitor and detail pages)
