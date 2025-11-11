# LangGraph Agentic System Integration

This document describes the LangGraph-based multi-agent disruption analysis system that has been integrated into the runwayops_demo application.

## Overview

The agentic system uses **LangGraph** to orchestrate multiple specialized AI agents that analyze flight disruptions, provide what-if scenarios, and generate actionable recommendations with full transparency and audit trails.

### Architecture

```
Flight Monitor Data
        ↓
┌─────────────────────────────────────────────┐
│   Predictive Signal Generator (ML Node)    │
│   • Analyzes delays, critical flights       │
│   • Calculates risk probability            │
│   • Decides: disruption detected?          │
└─────────────────┬───────────────────────────┘
                  ↓
        ┌─────────────────┐
        │  Orchestrator   │ (LLM-powered)
        │  • Main plan    │
        │  • What-if sims │
        └────────┬────────┘
                 ↓
    ┌────────────┴────────────┐
    ↓            ↓             ↓
┌────────┐  ┌───────────┐  ┌─────────┐  ┌───────┐
│  Risk  │  │ Rebooking │  │ Finance │  │ Crew  │
│ Agent  │  │   Agent   │  │  Agent  │  │ Agent │
└────┬───┘  └─────┬─────┘  └────┬────┘  └───┬───┘
     └────────────┴─────────────┴───────────┘
                    ↓
            ┌──────────────┐
            │  Aggregator  │
            │ • Final plan │
            │ • Audit log  │
            └──────────────┘
                    ↓
            MongoDB Persistence
```

### Key Features

1. **Multi-Agent Orchestration**: Specialized agents for risk, rebooking, finance, and crew management
2. **What-If Scenarios**: Simulates alternative outcomes (e.g., delay >3hrs, crew unavailable)
3. **Transparent Reasoning**: Every agent's input, output, and reasoning is logged
4. **Audit Trail**: Immutable logs persisted to MongoDB for compliance and replay
5. **Production-Ready**: Built on LangGraph, designed for scalability and reliability

## Installation & Setup

### 1. Install Dependencies

```bash
cd backend
uv pip install -r requirements.txt
```

New dependencies added:
- `langgraph==0.2.45` - Graph-based agent orchestration
- `langchain-core==0.3.15` - Core LangChain functionality
- `langchain-openai==0.2.8` - OpenAI LLM integration
- `pydantic==2.9.2` - Data validation

### 2. Configure Environment

Copy and update your `.env` file:

```bash
cp backend/.env.example backend/.env
```

Required configuration in `backend/.env`:

```bash
# Enable agentic system
AGENTIC_ENABLED=true

# Choose LLM provider (openai, openrouter, deepseek, gemini)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.2

# Provider API keys (configure the one you're using)
OPENAI_API_KEY=sk-your-openai-key
# OPENROUTER_API_KEY=sk-or-your-key
# DEEPSEEK_API_KEY=sk-your-deepseek-key
# GEMINI_API_KEY=your-gemini-key

# MongoDB for audit logs (already configured)
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=runwayops
```

**Multiple LLM Provider Support**: The system supports OpenAI, OpenRouter, DeepSeek, and Google Gemini. See [LLM_PROVIDERS.md](./LLM_PROVIDERS.md) for detailed configuration and cost comparison.

### 3. Start the System

Use the existing dev script:

```bash
./run_dev.sh
```

This starts:
- Backend (FastAPI) on `http://localhost:8000`
- Frontend (Vite) on `http://localhost:3000`

## API Endpoints

### Check Status

```bash
GET /api/agentic/status
```

Returns agentic system configuration and availability.

**Response:**
```json
{
  "enabled": true,
  "llm_model": "gpt-4o",
  "llm_temperature": 0.2,
  "api_key_configured": true,
  "mongo_configured": true
}
```

### Run Analysis

```bash
POST /api/agentic/analyze?airport=HKG&carrier=CX&mode=synthetic
```

Executes the full LangGraph workflow on current flight data.

**Response:**
```json
{
  "airport": "HKG",
  "carrier": "CX",
  "mode": "synthetic",
  "agentic_analysis": {
    "final_plan": {
      "disruption_detected": true,
      "risk_assessment": { ... },
      "rebooking_plan": { ... },
      "finance_estimate": { ... },
      "crew_rotation": { ... },
      "what_if_scenarios": [ ... ],
      "recommended_action": "PROCEED",
      "confidence": "high",
      "priority": "critical"
    },
    "audit_log": [ ... ],
    "disruption_detected": true
  },
  "original_data": { ... }
}
```

### Get Analysis History

```bash
GET /api/agentic/history?airport=HKG&carrier=CX&limit=10
```

Retrieves past analyses from MongoDB.

### Get Simulation History

```bash
GET /api/agentic/simulations?airport=HKG&carrier=CX&limit=10
```

Retrieves historical what-if simulations.

## Frontend Usage

### Dashboard Integration

The agentic analysis is integrated into the **Realtime Flight Monitor** dashboard:

1. **Status Check**: On mount, checks if agentic mode is enabled
2. **AI Analysis Button**: Appears in TopNav when enabled
3. **AI Analysis Tab**: New tab shows analysis results with visual components

### UI Components

- **AgenticAnalysisPanel**: Main visualization component
  - Disruption status banner
  - Key metrics grid (risk, cost, pax, crew)
  - What-if scenarios cards
  - Detailed plans for rebooking and risk
  - Audit trail summary

### User Flow

1. User views flight monitor data (synthetic or realtime)
2. Clicks "Run AI Analysis" button
3. LangGraph workflow executes (~5-15 seconds)
4. Results displayed in "AI Analysis" tab
5. User can review:
   - Risk assessment with probability
   - Financial impact estimates
   - Rebooking recommendations
   - What-if scenario comparisons
   - Transparent reasoning from each agent

## Code Structure

### Backend

```
backend/app/
├── agents/                      # LangGraph workflow
│   ├── __init__.py
│   ├── state.py                 # AgentState TypedDict
│   ├── nodes.py                 # Agent nodes (predictive, orchestrator, sub-agents)
│   └── workflow.py              # DisruptionWorkflow graph
├── routes/
│   └── agentic.py               # FastAPI endpoints
├── services/
│   └── agentic.py               # Service layer + MongoDB persistence
└── config.py                    # Settings with agentic config
```

### Frontend

```
frontend/dashboard/src/
├── hooks/
│   └── useAgenticAnalysis.ts    # Hook for API calls
├── components/
│   └── AgenticAnalysisPanel.tsx # Main visualization component
└── views/
    └── RealtimeFlightMonitor.tsx # Updated with agentic tab
```

## Agent Descriptions

### Predictive Signal Generator

- **Role**: First-stage detector
- **Input**: Flight monitor payload (stats, flights, alerts)
- **Logic**: Analyzes delays, critical flights, risk probability
- **Output**: `disruption_detected: bool`, risk metrics
- **Note**: Mock implementation; replace with LSTM model in production

### Orchestrator Agent

- **Role**: Strategic decision-maker
- **Type**: LLM-powered (GPT-4o)
- **Responsibilities**:
  - Assess disruption severity
  - Generate main action plan
  - Simulate 2+ what-if scenarios
- **Output**: Main plan + what-if scenarios array

### Risk Agent

- **Role**: Risk assessment specialist
- **Type**: LLM-powered
- **Output**: Likelihood, duration, passenger impact, regulatory implications (EU261/HKCAD)

### Rebooking Agent

- **Role**: Passenger re-accommodation
- **Type**: LLM-powered
- **Output**: Rebooking strategy, hotel requirements, VIP prioritization, affected pax count

### Finance Agent

- **Role**: Cost estimation
- **Type**: LLM-powered
- **Output**: Compensation costs, hotel/meals, operational costs, total impact

### Crew Agent

- **Role**: Crew scheduling and compliance
- **Type**: LLM-powered
- **Output**: Crew changes needed, backup requirements, regulatory issues

### Aggregator

- **Role**: Final synthesis
- **Logic**: Combines all agent outputs, prioritizes actions, finalizes plan
- **Output**: Complete `final_plan` with confidence and priority levels

## MongoDB Collections

### `agent_audit_logs`

Stores complete reasoning traces for transparency and compliance.

**Schema:**
```javascript
{
  timestamp: ISODate,
  airport: "HKG",
  carrier: "CX",
  disruption_detected: true,
  audit_log: [
    {
      agent: "Predictive",
      input: { ... },
      output: { ... },
      timestamp: "2025-11-11T..."
    },
    ...
  ],
  final_plan: { ... }
}
```

### `agent_simulations`

Stores what-if scenario results for historical comparison.

**Schema:**
```javascript
{
  timestamp: ISODate,
  airport: "HKG",
  carrier: "CX",
  scenarios: [
    {
      scenario: "delay_3hr",
      plan: { description: "...", actions: [...] }
    },
    ...
  ],
  risk_assessment: { ... },
  final_plan: { ... }
}
```

## Testing

### Manual Testing

1. **Enable synthetic mode** (no API quotas):
```bash
# In backend/.env
AGENTIC_ENABLED=true
OPENAI_API_KEY=sk-your-key
FLIGHT_MONITOR_MODE=synthetic
```

2. **Start system**:
```bash
./run_dev.sh
```

3. **Open dashboard**: `http://localhost:3000`

4. **Run analysis**:
   - Click "Run AI Analysis" button
   - Wait for workflow completion
   - View results in "AI Analysis" tab

5. **Verify MongoDB persistence**:
```bash
mongosh
use runwayops
db.agent_audit_logs.find().limit(1).pretty()
db.agent_simulations.find().limit(1).pretty()
```

### Testing with Realtime Data

```bash
# In backend/.env
FLIGHT_MONITOR_MODE=realtime
AVIATIONSTACK_API_KEY=your-key
```

Workflow will analyze live flight data from aviationstack API.

## Production Considerations

### 1. LLM API Costs

- Each analysis makes 5-6 LLM calls (orchestrator + sub-agents)
- Estimated cost per analysis: $0.10-0.30 (GPT-4o)
- **Mitigation**: Cache results, rate-limit analysis triggers

### 2. Latency

- Typical workflow execution: 5-15 seconds
- Sub-agents run in parallel (LangGraph feature)
- **Mitigation**: Consider async/background processing for production

### 3. LLM Reliability

- JSON parsing can fail if LLM returns non-JSON
- **Mitigation**: Fallback logic implemented in all agents
- Consider structured output mode (OpenAI function calling)

### 4. Scalability

- LangGraph is production-ready
- **Deployment options**:
  - Self-hosted container
  - AWS Lambda (for event-driven)
  - LangGraph Cloud (managed)

### 5. Security

- Store `OPENAI_API_KEY` securely (never commit)
- Use environment variables or secret management
- Audit logs contain flight data - ensure MongoDB access controls

## Extending the System

### Adding a New Agent

1. **Create agent node** in `backend/app/agents/nodes.py`:
```python
def my_new_agent_node(state: AgentState) -> AgentState:
    llm = get_llm()
    # ... agent logic
    result = { ... }
    state = log_reasoning(state, "MyAgent", input, result)
    state["my_new_field"] = result
    return state
```

2. **Update state** in `backend/app/agents/state.py`:
```python
class AgentState(TypedDict):
    # ... existing fields
    my_new_field: Dict[str, Any]
```

3. **Wire into graph** in `backend/app/agents/workflow.py`:
```python
graph.add_node("my_agent", my_new_agent_node)
graph.add_edge("orchestrator", "my_agent")
graph.add_edge("my_agent", "aggregator")
```

### Replacing Mock Predictive with ML Model

Replace the heuristic logic in `predictive_node` with actual model inference:

```python
def predictive_node(state: AgentState) -> AgentState:
    input_data = state["input_data"]
    
    # Load your trained LSTM/transformer model
    model = load_trained_model()
    
    # Extract features
    features = extract_features(input_data)
    
    # Run inference
    risk_prob = model.predict(features)
    detected = risk_prob > 0.7
    
    result = {
        "disruption_detected": detected,
        "risk_probability": float(risk_prob),
        "reasoning": f"ML model prediction: {risk_prob:.2f}"
    }
    
    state = log_reasoning(state, "Predictive", input_data, result)
    state["disruption_detected"] = detected
    state["risk_assessment"] = result
    
    return state
```

## Troubleshooting

### "Agentic analysis is not enabled"

- Ensure `AGENTIC_ENABLED=true` in `backend/.env`
- Restart backend after changing environment variables

### "OPENAI_API_KEY must be configured"

- Set valid OpenAI API key in `backend/.env`
- Verify key has not expired

### "Failed to fetch flight data"

- Check flight monitor provider is working
- Test `/api/flight-monitor` endpoint directly

### LLM returns non-JSON

- Check logs for raw LLM responses
- Agents have fallback logic but may produce generic results
- Consider using OpenAI structured output mode

### MongoDB connection errors

- Ensure MongoDB is running: `mongod --dbpath ./data/db`
- Check `MONGO_URI` in configuration

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Python](https://python.langchain.com/)
- [OpenAI API](https://platform.openai.com/docs)
- Original concept: `agentic_system.md`

## Summary

The LangGraph agentic system provides:
- ✅ Multi-agent disruption analysis
- ✅ What-if scenario simulation
- ✅ Transparent audit trails
- ✅ MongoDB persistence
- ✅ Full-stack integration (FastAPI + React)
- ✅ Production-ready architecture

Next steps: Test thoroughly, tune agent prompts, consider ML model replacement for predictive node, and monitor LLM costs in production.
