# AI-Generated "WHY This Option?" Reasoning

## Overview

The "WHY this option?" feature now displays **REAL AI agent decisions** from the multi-agent system, not hardcoded text.

## How It Works

When you click "Enable AI" in the Agent Console, the system:

1. **Runs APIV2 (ADK) Multi-Agent Workflow**:
   - Predictive Agent → Risk Agent → Rebooking Agent → Finance Agent → Crew Agent → Aggregator

2. **Extracts Agent Decisions** from each sub-agent:
   - **Risk Agent**: Disruption probability, passenger impact, duration
   - **Rebooking Agent**: Strategy, hotel requirements, passenger count
   - **Finance Agent**: Total cost, rebooking cost, compensation
   - **Crew Agent**: Crew availability, backup requirements

3. **Converts Agent Outputs to WHY Reasons**:
   - Parses the `audit_log` for each agent's reasoning
   - Extracts key decisions from each agent's output
   - Formats them into human-readable WHY statements

## Example WHY Reasons

### When No Disruption Detected:

**Option 1 - Primary:**
- ✓ Risk Agent: Low disruption risk (0%) - proactive options recommended
- ✓ Rebooking Agent: Standard rebooking - accommodates 96 passengers
- ✓ Finance Agent: $12,500 total cost (rebooking: $8,000, compensation: $0)
- ✓ Crew Agent: All crews available
- ✓ AI Optimization: Fastest route with highest success probability

**Option 2 - Alternative:**
- ✓ Risk Agent: Low disruption risk (0%) - proactive options recommended
- ✓ Rebooking Agent: Standard rebooking - accommodates 96 passengers
- ✓ Finance Agent: $12,500 total cost
- ✓ AI Optimization: Better capacity for group rebooking if primary route fills

### When Disruption Detected (Risk > 70%):

**Option 1 - Primary:**
- ⚠️ Risk Agent: 85% disruption probability detected - high passenger impact
- ✓ Rebooking Agent: Immediate alternative flight (hotel accommodation included) - accommodates 156 passengers
- 💰 Finance Agent: $142,000 total cost (rebooking: $85,000, compensation: $45,000)
- ⚠️ Crew Agent: Backup crew arranged - backup crew arranged
- ✓ AI Optimization: Fastest route with highest success probability

**Option 3 - Premium (if high risk):**
- ⚠️ Risk Agent: 85% disruption probability - high passenger impact  
- ✈️ Rebooking Agent: Next day premium upgrade - hotel included
- 💰 Finance Agent: $180,000 total cost (hotel: $25,000)
- ⭐ Business class upgrade due to extended delay
- 🏨 Hotel accommodation included ($25,000 budget)
- 🛡️ Guaranteed seats - no further disruption risk

## Agent Decision Flow

```
User Clicks "Enable AI"
        ↓
Frontend: POST /api/agent-options/passengers/{pnr}/options
        ↓
Backend: Runs APIV2 Workflow
        ↓
┌─────────────────────────────────────┐
│  Predictive Agent                   │
│  • Analyzes signals                 │
│  • Detects disruption: Yes/No       │
│  • Risk probability: 0-100%         │
└─────────────────────────────────────┘
        ↓ (if disruption detected)
┌─────────────────────────────────────┐
│  Parallel Sub-Agents:               │
│                                     │
│  Risk Agent:                        │
│  • Likelihood: high/medium/low      │
│  • Passenger impact: 150 pax        │
│  • Duration: 180 minutes            │
│  • Regulatory: EU261 required       │
│                                     │
│  Rebooking Agent:                   │
│  • Strategy: Immediate alternative  │
│  • Hotel required: Yes              │
│  • Estimated PAX: 150               │
│                                     │
│  Finance Agent:                     │
│  • Total cost: $142,000             │
│  • Rebooking: $85,000               │
│  • Compensation: $45,000            │
│  • Hotel/meals: $12,000             │
│                                     │
│  Crew Agent:                        │
│  • Crew available: No               │
│  • Backup required: Yes             │
│  • Status: Backup crew arranged     │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Aggregator Agent                   │
│  • Combines all agent outputs       │
│  • Creates final action plan        │
└─────────────────────────────────────┘
        ↓
Backend: _generate_options_from_analysis()
        ↓
┌─────────────────────────────────────┐
│  WHY Reason Generator               │
│  • Extracts agent decisions         │
│  • Converts to WHY statements       │
│  • Formats for UI display           │
└─────────────────────────────────────┘
        ↓
Frontend: Displays WHY reasons in accordion
```

## Code Changes

### Backend Changes

**File**: `backend/app/routes/agent_options.py`

**Key Functions**:

1. **`_generate_options_from_analysis()`**
   - Extracts real agent outputs instead of using hardcoded text
   - Logs agent decisions for debugging

2. **`_extract_agent_insights()`**
   - Parses `audit_log` for each agent's reasoning
   - Organizes outputs by agent type

3. **`_build_why_reasons_from_agents()`**
   - Converts agent decisions into WHY statements
   - Formats based on agent type (Risk/Rebooking/Finance/Crew)
   - Adapts reasoning based on disruption severity

### What Gets Logged

When you click "Enable AI", the backend terminal shows:

```
🎯 Extracting AI agent decisions for WHY reasoning:
   Risk Agent: Detailed risk assessment based on signals
   Rebooking: Immediate alternative flight
   Finance: $142,000
   Crew: Backup crew on standby
```

## Testing

### Test Case 1: No Disruption
1. Go to Agent Console
2. Select flight CX255, passenger AA145J
3. Click "Enable AI"
4. Expand "WHY this option?" on any card
5. **Expected**: See Risk Agent (0% probability), Rebooking Agent, Finance Agent decisions

### Test Case 2: With Disruption (using What-If)
1. Go to "What-If Analysis" tab
2. Select flight CX520
3. Set Weather: Severe, Crew: 5, Aircraft Issue: checked
4. Click "Run Analysis"
5. **Expected**: See 85% disruption probability
6. Go back to Agent Console
7. **Expected**: WHY reasons now show high risk, backup crew, higher costs

## Benefits

✅ **Transparency**: Users see actual AI reasoning, not marketing text
✅ **Accountability**: Each decision traced to specific agent
✅ **Trust**: Real data from Risk/Finance/Crew agents builds confidence
✅ **Debugging**: Logs show what each agent decided
✅ **Adaptability**: Reasoning changes based on actual situation

## Future Enhancements

1. **LLM-Generated Summaries**: Use LLM to convert agent outputs into natural language
2. **Confidence Scores**: Show how confident each agent is in their decision
3. **Agent Disagreement**: Highlight when agents have conflicting recommendations
4. **Historical Comparison**: Compare current decision to past similar situations
5. **User Feedback Loop**: Allow agents to learn from user selections
