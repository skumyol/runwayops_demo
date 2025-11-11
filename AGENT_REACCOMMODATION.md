# AI-Powered Reaccommodation with LangGraph Agents

## Overview

Your system now has **two ways** to get reaccommodation recommendations:

### 1. **Static Options** (Current System)
- **Source**: Pre-generated data in MongoDB
- **How**: `scripts/generate_mock_data.py` creates flight manifests with `options[]`
- **Pros**: Fast, deterministic, no API costs
- **Cons**: Not dynamic, no reasoning, no what-if analysis

### 2. **AI-Powered Suggestions** (New!)
- **Source**: LangGraph multi-agent workflow (Predictive → Orchestrator → Risk/Rebooking/Finance/Crew → Aggregator)
- **How**: Analyzes flight disruption in real-time with AI
- **Pros**: Dynamic, includes reasoning, what-if scenarios, adapts to context
- **Cons**: LLM API costs, slower (5-15 seconds)

## Architecture

```
AgentPassengerPanel (Frontend)
        ↓
   User clicks "Get AI Suggestions"
        ↓
/api/agent-reaccommodation/suggestions/{flight}
        ↓
Fetch MongoDB (manifest, passengers, crew, disruption)
        ↓
LangGraph Workflow Executes:
  ┌─────────────────────────────────┐
  │ 1. Predictive Signal Generator  │
  │    → Detect disruption?         │
  └──────────┬──────────────────────┘
             ↓ YES
  ┌─────────────────────────────────┐
  │ 2. Orchestrator (LLM)           │
  │    → Main plan + what-if sims   │
  └──────────┬──────────────────────┘
             ↓
  ┌─────────────────────────────────┐
  │ 3. Parallel Sub-Agents (LLMs)   │
  │    ├─ Risk Assessment           │
  │    ├─ Rebooking Strategy        │
  │    ├─ Financial Estimate        │
  │    └─ Crew Rotation             │
  └──────────┬──────────────────────┘
             ↓
  ┌─────────────────────────────────┐
  │ 4. Aggregator                   │
  │    → Final plan with confidence │
  └─────────────────────────────────┘
        ↓
Return AI suggestions to frontend
```

## API Endpoints

### 1. Get AI Suggestions (Simplified)

```http
GET /api/agent-reaccommodation/suggestions/{flight_number}?passenger_pnr={pnr}
```

**Purpose**: Get actionable AI recommendations for a flight or specific passenger.

**Example Request**:
```bash
curl http://localhost:8000/api/agent-reaccommodation/suggestions/CX888
```

**Example Response**:
```json
{
  "flightNumber": "CX888",
  "disruption_detected": true,
  "recommended_action": "PROCEED",
  "priority": "critical",
  "confidence": "high",
  "risk_level": "high",
  "estimated_cost": 45000.0,
  "rebooking_strategy": "Same-day alternative with premium protection",
  "affected_passengers": 156,
  "what_if_scenarios": [
    {
      "scenario": "delay_3hr",
      "plan": {
        "description": "If delay extends to 3+ hours",
        "actions": ["Activate hotel accommodation", "Increase compensation tier"]
      }
    }
  ],
  "reasoning": {
    "risk": "High probability of extended delay based on weather patterns...",
    "rebooking": "Priority rebooking for Diamond/Gold tier passengers...",
    "finance": "Estimated compensation costs based on EU261 regulations..."
  }
}
```

**With Passenger PNR**:
```bash
curl http://localhost:8000/api/agent-reaccommodation/suggestions/CX888?passenger_pnr=ABC123
```

Returns passenger-specific recommendation:
```json
{
  ...
  "passenger": {
    "pnr": "ABC123",
    "name": "John Smith",
    "tier": "Diamond",
    "specific_recommendation": "Priority rebooking with lounge access and compensation on same-day alternative flight"
  }
}
```

### 2. Full Agent Analysis

```http
POST /api/agent-reaccommodation/analyze/{flight_number}?force_refresh=false
```

**Purpose**: Run complete LangGraph workflow and get full audit trail.

**Example**:
```bash
curl -X POST http://localhost:8000/api/agent-reaccommodation/analyze/CX888
```

**Response** (includes full audit log):
```json
{
  "flightNumber": "CX888",
  "analysis": {
    "final_plan": { ... },
    "audit_log": [
      {
        "agent": "Predictive",
        "input": { ... },
        "output": { "disruption_detected": true, "risk_probability": 0.85 },
        "timestamp": "2025-11-11T13:05:00Z"
      },
      {
        "agent": "Orchestrator",
        "input": { ... },
        "output": { "main_plan": {...}, "what_if_scenarios": [...] },
        "timestamp": "2025-11-11T13:05:05Z"
      },
      ...
    ],
    "disruption_detected": true
  },
  "metadata": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "timestamp": "2025-11-11T13:05:12Z"
  }
}
```

### 3. Compare Static vs AI

```http
GET /api/agent-reaccommodation/compare/{flight_number}
```

**Purpose**: Side-by-side comparison of MongoDB options vs AI suggestions.

**Example**:
```bash
curl http://localhost:8000/api/agent-reaccommodation/compare/CX888
```

**Response**:
```json
{
  "flightNumber": "CX888",
  "static": {
    "source": "MongoDB pre-generated",
    "count": 3,
    "options": [
      { "id": "opt-1", "departureTime": "08:00", ... },
      { "id": "opt-2", "departureTime": "14:30", ... },
      { "id": "opt-3", "departureTime": "20:00", ... }
    ]
  },
  "ai_powered": {
    "source": "LangGraph (deepseek/deepseek-chat)",
    "suggestions": { ... }
  },
  "comparison": {
    "static_is_deterministic": true,
    "ai_is_dynamic": true,
    "ai_includes_reasoning": true,
    "ai_includes_what_if": true
  }
}
```

## Frontend Integration

### Add Button to AgentPassengerPanel

```tsx
import { useAgentReaccommodation } from '../hooks/useAgentReaccommodation';
import { Bot } from 'lucide-react';

export function AgentPassengerPanel() {
  const { flights, loading: flightsLoading } = useReaccommodationFlights();
  const [selectedFlight, setSelectedFlight] = useState<string | null>(null);
  
  // NEW: Add agent hook
  const {
    suggestions,
    loading: agentLoading,
    error: agentError,
    getSuggestions,
  } = useAgentReaccommodation();

  const handleGetAISuggestions = async () => {
    if (!selectedFlight) return;
    await getSuggestions(selectedFlight);
  };

  return (
    <div>
      {/* ... existing code ... */}
      
      {/* NEW: AI Suggestions Button */}
      <div className="p-6 border-t">
        <Button
          onClick={handleGetAISuggestions}
          disabled={!selectedFlight || agentLoading}
          className="w-full bg-indigo-600 hover:bg-indigo-700"
        >
          <Bot className="w-4 h-4 mr-2" />
          {agentLoading ? 'Running AI Analysis...' : 'Get AI Suggestions'}
        </Button>
        
        {agentError && (
          <p className="text-sm text-destructive mt-2">{agentError}</p>
        )}
        
        {suggestions && (
          <Card className="mt-4 p-4">
            <h4 className="font-semibold mb-2">AI Recommendations</h4>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-muted-foreground">Strategy:</span>
                <p className="font-medium">{suggestions.rebooking_strategy}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Priority:</span>
                <Badge>{suggestions.priority}</Badge>
              </div>
              <div>
                <span className="text-muted-foreground">Estimated Cost:</span>
                <span className="font-semibold">${suggestions.estimated_cost.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Confidence:</span>
                <span className="font-semibold">{suggestions.confidence}</span>
              </div>
            </div>
            
            {suggestions.reasoning && (
              <details className="mt-3">
                <summary className="cursor-pointer text-sm font-medium">
                  View AI Reasoning
                </summary>
                <div className="mt-2 text-xs space-y-2">
                  <div>
                    <strong>Risk:</strong> {suggestions.reasoning.risk}
                  </div>
                  <div>
                    <strong>Rebooking:</strong> {suggestions.reasoning.rebooking}
                  </div>
                  <div>
                    <strong>Finance:</strong> {suggestions.reasoning.finance}
                  </div>
                </div>
              </details>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
```

### Or Create Standalone Component

```tsx
import { useAgentReaccommodation } from '../hooks/useAgentReaccommodation';

export function AIRecommendationPanel({ flightNumber }: { flightNumber: string }) {
  const { suggestions, loading, error, getSuggestions } = useAgentReaccommodation();

  useEffect(() => {
    if (flightNumber) {
      getSuggestions(flightNumber);
    }
  }, [flightNumber, getSuggestions]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!suggestions) return null;

  return (
    <Card>
      <h3>AI-Powered Recommendations</h3>
      <div>
        <Badge variant={suggestions.disruption_detected ? 'destructive' : 'success'}>
          {suggestions.disruption_detected ? 'Disruption Detected' : 'No Disruption'}
        </Badge>
        <p>{suggestions.rebooking_strategy}</p>
        <p>Affected: {suggestions.affected_passengers} passengers</p>
        <p>Cost: ${suggestions.estimated_cost.toLocaleString()}</p>
      </div>
    </Card>
  );
}
```

## Testing

### 1. Enable Agentic System

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=deepseek  # or openai, openrouter, gemini
DEEPSEEK_API_KEY=sk-your-key
LLM_MODEL=deepseek-chat
```

### 2. Seed Flight Data

```bash
# Generate mock flights in MongoDB
cd backend
uv run python ../scripts/generate_mock_data.py --flights 5
```

### 3. Test Endpoints

```bash
# List available flights
curl http://localhost:8000/api/reaccommodation/flights

# Get AI suggestions for a flight
curl http://localhost:8000/api/agent-reaccommodation/suggestions/CX888

# Compare static vs AI
curl http://localhost:8000/api/agent-reaccommodation/compare/CX888
```

### 4. Test in UI

1. Start dev servers: `./run_dev.sh`
2. Navigate to Agent Console: http://localhost:3000
3. Select a flight from dropdown
4. Click "Get AI Suggestions" button
5. View AI recommendations vs static options

## Cost Estimates

Cost per flight analysis (5-6 LLM calls, ~15k tokens):

| Provider | Model | Cost |
|----------|-------|------|
| DeepSeek | deepseek-chat | **$0.004** ⭐ |
| Gemini | gemini-1.5-flash | **$0.004** ⭐ |
| OpenAI | gpt-3.5-turbo | $0.02 |
| Gemini | gemini-1.5-pro | $0.05 |
| OpenAI | gpt-4o | $0.10 |
| OpenRouter | claude-3.5-sonnet | $0.15 |

**Recommendation**: Use DeepSeek or Gemini Flash for development/testing to minimize costs.

## Benefits Over Static Options

| Feature | Static (MongoDB) | AI-Powered |
|---------|------------------|------------|
| **Speed** | Instant | 5-15 seconds |
| **Cost** | Free | $0.004-$0.15 per flight |
| **Reasoning** | None | Full transparency |
| **What-if Scenarios** | No | Yes |
| **Context-Aware** | No | Yes (tier, PRM, weather) |
| **Dynamic** | No | Adapts to live data |
| **Audit Trail** | No | Complete agent logs |
| **Confidence Scores** | No | Yes |

## Best Practices

1. **Cache Results**: Store AI suggestions in MongoDB to avoid repeated API calls
2. **Fallback**: Show static options if AI call fails
3. **Async**: Run AI analysis in background, don't block UI
4. **Progressive**: Show static options first, then enhance with AI
5. **Cost Control**: Set rate limits or use cheaper models for dev

## Next Steps

1. **Add caching layer** to avoid re-analyzing same flight
2. **Create comparison UI** showing static vs AI side-by-side
3. **Add passenger-specific button** in passenger detail view
4. **Enable agent selection** for specific sub-tasks (e.g., only finance estimate)
5. **Add feedback loop** to improve agent prompts based on human agent corrections

## Summary

**Where do recommendations come from?**
- **Currently**: Static pre-generated data in MongoDB (`options` field)
- **Now available**: Real-time AI analysis via LangGraph multi-agent workflow

**Can you manually call agents from frontend?**
- **Yes!** Use the new endpoints and `useAgentReaccommodation` hook
- Three ways: suggestions (simple), full analysis (detailed), comparison (side-by-side)
- Just add a button that calls `getSuggestions(flightNumber)` or `analyzeFlightWithAgents(flightNumber)`

Your system now has both deterministic (fast, free) and AI-powered (smart, insightful) options! 🚀
