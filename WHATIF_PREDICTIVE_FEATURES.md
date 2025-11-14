# What-If Scenarios & Periodic Predictive Updates

## Overview

Two new features have been implemented:
1. **Periodic Predictive Updates** - Automatically predicts disruptions and stops when disruption occurs
2. **What-If Scenario Analysis** - Simulate different scenarios to see predicted outcomes

## 1. Periodic Predictive Updates

### Backend Service

**File**: `backend/app/services/predictive_monitor.py`

**Features**:
- Runs predictive agent periodically (default: every 60 seconds)
- Automatically skips prediction if disruption already confirmed/active/resolved
- Stores predictions in memory for quick retrieval
- Can be started/stopped programmatically

**Key Methods**:
```python
monitor = get_predictive_monitor()

# Start monitoring (runs in background)
await monitor.start()

# Predict disruption for specific flight
result = await monitor.predict_disruption(flight_data, force=False)

# Get latest prediction
prediction = monitor.get_prediction(flight_number)

# Stop monitoring
await monitor.stop()
```

**Smart Skip Logic**:
- If `disruption.status` is `confirmed`, `active`, or `resolved` → Skip prediction
- Log: `"⏭️  CX520: Disruption already confirmed, skipping prediction"`
- Returns existing disruption info without running agents

### API Endpoint

**GET** `/api/whatif/predict/{flight_number}`

**Parameters**:
- `airport` (default: HKG)
- `carrier` (default: CX)
- `mode` (synthetic/realtime/mongo)
- `force` (boolean) - Force prediction even if disruption exists

**Response**:
```json
{
  "flight_number": "CX520",
  "prediction": {
    "timestamp": "2025-11-14T12:40:00Z",
    "disruption_detected": true,
    "risk_assessment": { ... },
    "signal_breakdown": { ... }
  },
  "full_analysis": { ... }
}
```

**Or if skipped**:
```json
{
  "flight_number": "CX520",
  "prediction_skipped": true,
  "reason": "Disruption status: confirmed",
  "existing_disruption": { ... }
}
```

## 2. What-If Scenario Analysis

### Backend Endpoint

**POST** `/api/whatif/analyze`

**Request Body**:
```json
{
  "flight_number": "CX520",
  "delay_minutes": 60,
  "weather_impact": "severe",
  "crew_unavailable": 3,
  "aircraft_issue": true,
  "passenger_count_change": -50,
  "connection_pressure": "high"
}
```

**All scenario parameters are optional** - specify only what you want to change.

**Response**:
```json
{
  "scenario": { ... },
  "baseline": {
    "statusCategory": "warning",
    "delayMinutes": 15,
    "paxImpacted": 96
  },
  "predicted_outcome": {
    "disruption_detected": true,
    "risk_assessment": {
      "likelihood": "high",
      "impact_score": 0.92
    },
    "final_plan": {
      "priority": "critical",
      "confidence": "high",
      "finance_estimate": {
        "total_usd": 142000
      },
      "rebooking_plan": {
        "strategy": "immediate_alternative",
        "affected_pax_count": 146
      }
    }
  },
  "comparison": {
    "risk_change": {
      "baseline": "warning",
      "predicted": "critical"
    },
    "financial_impact": 142000,
    "passengers_affected": 146,
    "recommended_actions": [...]
  }
}
```

### Frontend UI Component

**File**: `frontend/dashboard/src/views/WhatIfScenario.tsx`

**Access**: Top navigation → "What-If Analysis" tab (🧪 icon)

**Features**:
1. **Flight Selection** - Choose any flight from current data
2. **Scenario Configuration**:
   - Additional delay slider (0-180 minutes)
   - Weather impact dropdown (none/minor/moderate/severe)
   - Crew unavailable slider (0-10 people)
   - Aircraft issue checkbox
   - Connection pressure (low/medium/high)

3. **Results Display**:
   - Disruption likelihood
   - Risk level comparison (baseline → predicted)
   - Financial impact estimate
   - Passengers affected count
   - Recommended actions

**UI Features**:
- Real-time baseline status display
- Interactive sliders and dropdowns
- Visual risk comparison
- Loading states with animations
- Toast notifications for success/error

## How It Works

### Periodic Predictions Flow

```
1. PredictiveMonitor starts background task
   ↓
2. Every 60 seconds, check active flights
   ↓
3. For each flight:
   - Check if disruption already exists
   - If status is confirmed/active/resolved → SKIP
   - Otherwise → Run predictive agent
   ↓
4. Store prediction with timestamp
   ↓
5. Prediction available via API
```

### What-If Analysis Flow

```
1. User selects flight in UI
   ↓
2. UI displays baseline status
   ↓
3. User adjusts scenario parameters
   ↓
4. Click "Run Analysis"
   ↓
5. Frontend sends POST to /api/whatif/analyze
   ↓
6. Backend:
   - Fetches current flight data
   - Applies scenario modifications
   - Runs APIV2 (ADK) agents with modified data
   - Returns predicted outcome
   ↓
7. Frontend displays:
   - Risk comparison
   - Financial impact
   - Recommended actions
```

## Example Usage

### Backend: Periodic Predictions

```python
from app.services.predictive_monitor import get_predictive_monitor

# In your startup event
monitor = get_predictive_monitor()
await monitor.start()

# Manual prediction
flight_data = {
    "flight_number": "CX520",
    "airport": "HKG",
    "carrier": "CX",
    "stats": {...},
    "flights": [...],
    "disruption": None  # or existing disruption
}

result = await monitor.predict_disruption(flight_data)

if result.get("prediction_skipped"):
    print(f"Skipped: {result['reason']}")
else:
    print(f"Predicted: {result['prediction']}")
```

### Frontend: What-If Scenario

```typescript
// User selects CX520 and adjusts:
// - Add 60min delay
// - Severe weather
// - 3 crew unavailable

const scenario = {
  flight_number: "CX520",
  delay_minutes: 60,
  weather_impact: "severe",
  crew_unavailable: 3
};

const response = await fetch('/api/whatif/analyze', {
  method: 'POST',
  body: JSON.stringify(scenario)
});

const result = await response.json();

// Shows:
// - Risk: warning → critical
// - Financial Impact: $142,000
// - Passengers Affected: 146
// - Actions: ["Immediate rebooking required", ...]
```

## Key Differences

### Predictive Updates vs What-If Analysis

| Feature | Predictive Updates | What-If Analysis |
|---------|-------------------|------------------|
| **Purpose** | Automatically monitor for disruptions | Test hypothetical scenarios |
| **Trigger** | Automatic (periodic) | Manual (user-initiated) |
| **Modification** | Uses actual data | Uses modified data |
| **Skip Logic** | Yes (stops when disruption confirmed) | No (always runs) |
| **Use Case** | Early warning system | Decision support |
| **Output** | Prediction stored | Scenario comparison |

## Configuration

### Backend

**Environment Variables** (none required - uses defaults):
```bash
# Predictive monitor update interval can be configured in code
# Default: 60 seconds
```

**In code**:
```python
# Custom update interval
monitor = PredictiveMonitor(update_interval_seconds=30)
```

### Frontend

No configuration needed - uses existing `VITE_MONITOR_API` setting.

## API Reference

### Periodic Predictions

**GET** `/api/whatif/predict/{flight_number}`
- Returns prediction or skip reason
- Automatically skips if disruption already exists
- Can force prediction with `force=true`

### What-If Analysis

**POST** `/api/whatif/analyze`
- Accepts scenario modifications
- Returns predicted outcome vs baseline
- Never modifies actual flight data

## Testing

### Test Periodic Predictions

```bash
# Get prediction for CX520
curl "http://localhost:8000/api/whatif/predict/CX520?airport=HKG&carrier=CX"

# Force prediction even if disruption exists
curl "http://localhost:8000/api/whatif/predict/CX520?force=true"
```

### Test What-If Scenarios

```bash
# Test with additional delay
curl -X POST "http://localhost:8000/api/whatif/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_number": "CX520",
    "delay_minutes": 60,
    "weather_impact": "severe"
  }'
```

### Test in UI

1. Navigate to http://localhost:3000
2. Click "What-If Analysis" tab in top navigation
3. Select a flight (e.g., CX520)
4. Adjust scenario parameters:
   - Add 60min delay
   - Set weather to "Severe"
   - Set 3 crew unavailable
5. Click "Run Analysis"
6. View predicted outcome

## Logging

Both features include comprehensive logging:

```
🔮 WHAT-IF SCENARIO: CX520
================================================================================
📊 Baseline: critical - 34min delay
🎭 Scenario modifications applied:
   ⏱️  Additional delay: +60min
   🌧️  Weather: severe
   👥 Crew unavailable: 3
🚀 Running agent analysis on scenario...
✅ What-if analysis complete
```

```
🔮 CX520: Running predictive analysis...
✅ CX520: Prediction complete - Disruption: True
```

Or:
```
⏭️  CX520: Disruption already confirmed, skipping prediction
```

## Files Created/Modified

### Backend
- ✨ **NEW**: `backend/app/services/predictive_monitor.py`
- ✨ **NEW**: `backend/app/routes/whatif.py`
- 📝 **MODIFIED**: `backend/app/main.py` (added whatif router)

### Frontend
- ✨ **NEW**: `frontend/dashboard/src/views/WhatIfScenario.tsx`
- 📝 **MODIFIED**: `frontend/dashboard/src/App.tsx` (added What-If tab)

## Future Enhancements

1. **Persistent Predictions**: Store predictions in database for historical analysis
2. **Batch Predictions**: Predict all flights at once
3. **Scenario Templates**: Pre-defined scenarios (e.g., "Typhoon", "Crew Strike")
4. **Comparison Mode**: Compare multiple scenarios side-by-side
5. **Export Results**: Download scenario analysis as PDF/CSV
6. **Scheduled Predictions**: Configure custom prediction schedules per flight
7. **Alert Thresholds**: Notify when prediction crosses certain risk levels
