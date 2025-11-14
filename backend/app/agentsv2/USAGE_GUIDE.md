# ADK Agents v2 - Usage Guide

Complete guide for using the Google ADK-based flight disruption management system.

## Quick Start

### 1. Installation

The ADK package is already added to `requirements.txt`. Install dependencies:

```bash
cd backend
uv pip install -r requirements.txt
```

Or using the project's UV package manager:

```bash
cd backend
uv sync
```

### 2. Start the Development Server

Use the provided run script:

```bash
./run_dev.sh
```

This will:
- Kill any processes on ports 8000 and 3000
- Warm up UV cache
- Start the FastAPI backend on port 8000
- Start the Vite frontend on port 3000

### 3. Verify Installation

Check that the ADK endpoints are available:

```bash
curl http://localhost:8000/api/v2/agents/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ADK Disruption Workflow",
  "workflow": "DisruptionWorkflowADK"
}
```

## API Endpoints

### 1. Health Check

**GET** `/api/v2/agents/health`

Check if the ADK workflow is running properly.

```bash
curl http://localhost:8000/api/v2/agents/health
```

### 2. Workflow Information

**GET** `/api/v2/agents/info`

Get details about agents, tools, and features.

```bash
curl http://localhost:8000/api/v2/agents/info
```

Response:
```json
{
  "workflow": "DisruptionWorkflowADK",
  "framework": "Google Agent Development Kit (ADK)",
  "agents": [
    "PredictiveAgent",
    "OrchestratorAgent",
    "RiskAgent",
    "RebookingAgent",
    "FinanceAgent",
    "CrewAgent",
    "AggregatorAgent"
  ],
  "tools": [
    "predictive_signal_tool",
    "rebooking_tool",
    "finance_tool",
    "crew_scheduling_tool"
  ],
  "features": [...]
}
```

### 3. Analyze Disruption

**POST** `/api/v2/agents/analyze`

Run the multi-agent workflow to analyze flight disruptions.

#### Request Format

```bash
curl -X POST http://localhost:8000/api/v2/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "airport": "HKG",
    "carrier": "CX",
    "timestamp": "2024-11-14T10:00:00Z",
    "stats": {
      "totalFlights": 45,
      "delayedFlights": 12,
      "paxImpacted": 350,
      "avgDelay": 125,
      "weatherScore": 0.75,
      "aircraftScore": 0.65,
      "crewScore": 0.55
    },
    "flights": [
      {
        "id": "CX888",
        "number": "CX888",
        "origin": "HKG",
        "destination": "JFK",
        "scheduledDeparture": "2024-11-14T14:00:00Z",
        "estimatedDeparture": "2024-11-14T16:30:00Z",
        "status": "delayed",
        "statusCategory": "critical",
        "delayMinutes": 150,
        "passengers": 250
      }
    ],
    "alerts": [
      {
        "type": "weather",
        "severity": "high",
        "message": "Severe thunderstorms in area"
      }
    ]
  }'
```

#### Response Format

```json
{
  "success": true,
  "disruption_detected": true,
  "final_plan": {
    "disruption_detected": true,
    "priority": "high",
    "recommended_action": "PROCEED",
    "risk_assessment": {...},
    "rebooking_plan": {...},
    "finance_estimate": {...},
    "crew_rotation": {...},
    "what_if_scenarios": [...],
    "confidence": "high"
  },
  "risk_assessment": {
    "risk_probability": 0.75,
    "disruption_detected": true,
    "likelihood": 0.75,
    "duration_minutes": 180,
    "pax_impact": "high",
    "regulatory_risk": "EU261/HKCAD compensation required"
  },
  "rebooking_plan": {
    "strategy": "next_day_alternate",
    "hotel_required": true,
    "vip_priority": true,
    "estimated_pax": 350,
    "actions": [
      "Book hotels for 350 passengers",
      "Arrange meal vouchers",
      "Prioritize 35 VIP passengers for rebooking",
      "Search alternative flights for 350 passengers",
      "Notify passengers via SMS/email"
    ]
  },
  "finance_estimate": {
    "compensation_usd": 210000,
    "hotel_meals_usd": 52500,
    "operational_usd": 25000,
    "total_usd": 287500,
    "breakdown": [...]
  },
  "crew_rotation": {
    "crew_changes_needed": true,
    "backup_crew_required": 2,
    "regulatory_issues": [
      "Crew duty time approaching limit",
      "Rest requirements must be maintained"
    ]
  },
  "simulation_results": [
    {
      "scenario": "delay_3hr",
      "plan": {
        "description": "Extended delay requiring hotels",
        "actions": [...]
      }
    },
    {
      "scenario": "crew_unavailable",
      "plan": {
        "description": "Crew duty limit exceeded",
        "actions": [...]
      }
    }
  ],
  "audit_log": [
    {
      "agent": "PredictiveAgent",
      "timestamp": "2024-11-14T10:00:00.123456",
      "input": {...},
      "output": {...}
    },
    ...
  ]
}
```

## Python API

### Direct Workflow Execution

```python
import asyncio
from app.agentsv2 import DisruptionWorkflowADK

# Initialize workflow
workflow = DisruptionWorkflowADK()

# Prepare flight data
flight_data = {
    "airport": "HKG",
    "carrier": "CX",
    "stats": {
        "weatherScore": 0.75,
        "aircraftScore": 0.65,
        "crewScore": 0.55,
        "paxImpacted": 350
    },
    "flights": [...]
}

# Run workflow (async)
result = await workflow.run(flight_data)

# Or run synchronously
result = workflow.run_sync(flight_data)

# Access results
if result['disruption_detected']:
    print(f"Priority: {result['final_plan']['priority']}")
    print(f"Cost: ${result['finance_estimate']['total_usd']:,}")
```

### Using Convenience Function

```python
from app.agentsv2.workflow import run_disruption_workflow

result = await run_disruption_workflow(flight_data)
```

## Testing

### Run Integration Test

```bash
cd backend
python -m app.agentsv2.test_integration
```

This will:
- Run the workflow with mock data
- Display detailed results
- Save output to `test_result.json`

### Expected Output

```
================================================================================
🧪 Starting ADK Workflow Integration Test
================================================================================
✅ Workflow initialized

================================================================================
🧠 PREDICTIVE AGENT (ADK): Starting disruption analysis...
================================================================================
🎯 Risk Probability: 75.00% | Disruption: DETECTED ✓

🎯 ORCHESTRATOR AGENT (ADK): Coordinating response...
⚡ Decision: Intervention=Yes, Severity=high

🔄 Running parallel sub-agents...
⚠️  RISK AGENT (ADK): Assessing likelihood and impact...
✈️  REBOOKING AGENT (ADK): Planning re-accommodation...
💰 FINANCE AGENT (ADK): Calculating costs...
👥 CREW AGENT (ADK): Managing crew schedules...
✅ Parallel sub-agents complete

📋 AGGREGATOR AGENT (ADK): Synthesizing final plan...
✅ Final Plan: Priority=high, Action=PROCEED

================================================================================
📋 WORKFLOW RESULTS
================================================================================
🎯 Disruption Detected: True
⚠️  Priority: high
🎬 Action: PROCEED

📊 Risk Assessment:
  - Likelihood: 75.00%
  - Duration: 180 minutes
  - Impact: high

✈️  Rebooking Plan:
  - Strategy: next_day_alternate
  - Hotel Required: True
  - Affected Passengers: 350

💰 Financial Impact:
  - Total Cost: $287,500
  - Compensation: $210,000
  - Hotel/Meals: $52,500

👥 Crew Management:
  - Changes Needed: True
  - Backup Crew: 2

🔮 What-If Scenarios: 2
  1. delay_3hr
  2. crew_unavailable

📝 Audit Log: 7 entries
================================================================================
✅ Integration Test Complete
================================================================================
```

## Validation Using UV

After making changes, validate the code:

```bash
# Check Python syntax
cd backend
uv run python -m py_compile app/agentsv2/*.py

# Run the integration test
uv run python -m app.agentsv2.test_integration

# Start the server and test endpoints
./run_dev.sh --check  # Check if already running
./run_dev.sh          # Start if not running
```

## Comparing with LangGraph Implementation

| Feature | LangGraph (v1) | ADK (v2) |
|---------|----------------|----------|
| **Endpoint** | `/api/agentic/*` | `/api/v2/agents/*` |
| **State Type** | `TypedDict` | `Pydantic BaseModel` |
| **Orchestration** | Graph nodes/edges | Agent hierarchy |
| **Parallelization** | Graph edges | `asyncio.gather` (→ ParallelAgent) |
| **Tools** | LangChain tools | Custom async tools |
| **LLM** | Via langchain | Direct (→ google.genai) |

Both implementations produce the same output structure and can run side-by-side.

## Migration Path to Full ADK

The current implementation uses **ADK-compatible patterns** without requiring the full ADK package. To migrate to native ADK:

1. **Install ADK**:
   ```bash
   uv pip install google-adk google-cloud-aiplatform
   ```

2. **Update agents.py**:
   ```python
   from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
   
   predictive_agent = LlmAgent(
       name="predictive_agent",
       model="gemini-2.5-flash",
       instruction="Analyze flight signals and detect disruptions",
       tools=[predictive_signal_tool]
   )
   ```

3. **Update workflow.py**:
   ```python
   workflow = SequentialAgent(
       name="disruption_workflow",
       sub_agents=[
           predictive_agent,
           orchestrator_agent,
           ParallelAgent(
               name="sub_agents",
               sub_agents=[risk_agent, rebooking_agent, finance_agent, crew_agent]
           ),
           aggregator_agent
       ]
   )
   ```

4. **Configure Vertex AI**:
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export GOOGLE_CLOUD_LOCATION=us-central1
   export GOOGLE_GENAI_USE_VERTEXAI=True
   ```

## Troubleshooting

### Port Already in Use

```bash
./run_dev.sh
# Script will automatically kill processes on ports 8000 and 3000
```

### Import Errors

```bash
cd backend
uv pip install -r requirements.txt
```

### Workflow Fails

Check logs in the terminal where `./run_dev.sh` is running. Look for:
- `❌` error markers
- Exception stack traces
- Agent-specific logs (`🧠`, `🎯`, `⚠️`, etc.)

### API Returns 500

```bash
# Check health endpoint
curl http://localhost:8000/api/v2/agents/health

# Check logs
tail -f backend/logs/app.log
```

## Next Steps

1. **Integrate with Frontend**: Update dashboard to call `/api/v2/agents/analyze`
2. **Add Real APIs**: Integrate Amadeus/Sabre for actual rebooking
3. **Deploy to Vertex AI**: Containerize and deploy to Google Cloud
4. **Add Monitoring**: Integrate with Cloud Logging and Monitoring
5. **Implement Caching**: Use ADK's context caching for performance

## References

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Implementation README](./README.md)
- [Design Document](../../../google_a2a_agents_apiV2.md)
