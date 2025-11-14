# Agent Console & WHY Feature Explanation

## Current Issues

### 1. Agent Console Shows Nothing

**Location**: Top navigation → "Agent Console" tab

**Why it's empty**:
- The Agent Console (`AgentPassengerPanel.tsx`) is designed for **passenger reaccommodation workflow**
- It requires flight disruption data with affected passengers
- Currently shows "No passenger data available" because:
  - It fetches from `/api/reaccommodation/flights` endpoint
  - This endpoint may not have test data configured
  - The mock data system may not be generating passenger manifests

**What it should show**:
- List of disrupted flights
- Passenger manifest for selected flight
- Reaccommodation options for each passenger
- Agent-powered option analysis
- "WHY this option?" reasoning for recommendations

### 2. "WHY this option?" Not Visible

**Location**: Agent Console → Select passenger → Option cards

**Why it doesn't show**:
- The "WHY this option?" accordion (`OptionCard.tsx` line 113-127) only displays if:
  1. A flight is selected
  2. A passenger is selected from that flight
  3. Reaccommodation options are available for that passenger
  4. Each option has `whyReasons` array populated

**What it should contain**:
- Explanations like:
  - "Matches passenger's Marco Polo Gold tier"
  - "Fastest arrival time for connecting passengers"
  - "Cabin class preserved per policy"
  - "Lower revenue risk"
  - "Protected routing with alliance partner"

### 3. LangGraph Still Referenced

**Where it appears**:
- `frontend/dashboard/src/lib/agentic.ts` - Configuration for agentic engines
- `frontend/dashboard/src/views/RealtimeFlightMonitor.tsx` - LangGraph agent references
- `frontend/dashboard/src/views/AgentPassengerPanel.tsx` - Agent analysis system
- Dev Tools dropdown - "Agent runtime" selector

**Current engine options**:
1. **LangGraph (default)** - Local Python-based agent workflow
2. **APIV2** - Google A2A Agents + Gemini workflow

**Purpose**: 
- These are for AI-powered disruption analysis
- Different from the predictive signals system
- Used for complex multi-agent reasoning (finance, crew legality, rebooking)

## How to Fix These Issues

### Option A: Add Mock/Test Data for Agent Console

Create test data for the reaccommodation system:

```bash
# Add to scripts/generate_mock_data.py
# Generate passenger manifest with reaccommodation options
```

**Files to create/modify**:
- `mock/passenger_manifest_CX520.json`
- `mock/reaccommodation_options_CX520.json`
- Update backend to serve this data at `/api/reaccommodation/*` endpoints

### Option B: Hide Agent Console Tab (Quick Fix)

If the Agent Console feature isn't needed for the demo:

```typescript
// frontend/dashboard/src/App.tsx
// Comment out or remove the Agent Console tab
```

### Option C: Document It's a Placeholder

Add a clear message in the Agent Console explaining it needs configuration:

```typescript
// Add to AgentPassengerPanel.tsx
<Card className="p-8 text-center">
  <h3>Agent Console requires passenger reaccommodation data</h3>
  <p>Configure /api/reaccommodation endpoints to use this feature</p>
</Card>
```

## Understanding the System Architecture

### Predictive Signals (NEW - Just Implemented)
- **Purpose**: Detect disruption risk using heuristics
- **Location**: Flight Monitor → Alert modal
- **Trigger**: Click alert icon on disrupted flights
- **Backend**: `backend/app/services/disruption_updater.py`

### Agentic Analysis (EXISTING - LangGraph/APIV2)
- **Purpose**: Complex multi-agent reasoning for finance/rebooking
- **Location**: Flight Monitor → "AI Analysis" tab or "Run AI Analysis" button
- **Engines**: LangGraph (local) or APIV2 (Gemini)
- **Backend**: `backend/app/routes/agentic.py` and `backend/app/agentsv2/`

### Agent Console (EXISTING - Passenger Focus)
- **Purpose**: Individual passenger reaccommodation workflow
- **Location**: Top nav → "Agent Console" tab
- **Focus**: Per-passenger options with "WHY" reasoning
- **Backend**: `backend/app/routes/agent_reaccommodation.py`

## Recommendations

1. **For Demo Purposes**: 
   - Hide or disable the Agent Console tab
   - Focus on Flight Monitor + Predictive Signals
   - Keep Agentic Analysis for disruption-level insights

2. **For Full System**:
   - Populate Agent Console with real/mock passenger data
   - Ensure all three systems work together:
     - Predictive Signals: Early warning
     - Agentic Analysis: Disruption-level strategy
     - Agent Console: Passenger-level execution

3. **Remove LangGraph References** (if desired):
   - Currently LangGraph is a valid engine option
   - If you want to remove it completely, need to:
     - Update `lib/agentic.ts` to remove langgraph option
     - Update backend to disable langgraph routes
     - Update all UI references to agents

## Files Reference

### Agent Console
- `frontend/dashboard/src/views/AgentPassengerPanel.tsx` - Main console
- `frontend/dashboard/src/components/OptionCard.tsx` - Option cards with WHY accordion
- `frontend/dashboard/src/hooks/useAgentReaccommodation.ts` - Agent analysis hook
- `frontend/dashboard/src/hooks/useAgentOptions.ts` - Options fetching

### Agentic Analysis
- `frontend/dashboard/src/views/RealtimeFlightMonitor.tsx` - AI Analysis tab
- `frontend/dashboard/src/components/AgenticAnalysisPanel.tsx` - Analysis display
- `frontend/dashboard/src/lib/agentic.ts` - Engine configuration
- `backend/app/routes/agentic.py` - LangGraph route
- `backend/app/agentsv2/` - APIV2 implementation

### Predictive Signals (NEW)
- `frontend/dashboard/src/views/RealtimeFlightMonitor.tsx` - Alert modal
- `frontend/dashboard/src/hooks/usePredictiveAlerts.ts` - Fetch hook
- `backend/app/services/disruption_updater.py` - Signal computation
- `backend/app/main.py` - `/api/predictive-alerts/{flight}` endpoint
