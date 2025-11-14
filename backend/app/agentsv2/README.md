# ADK-Based Flight Disruption Management System

This directory contains a re-implementation of the flight disruption management multi-agent system using **Google's Agent Development Kit (ADK)**. It mirrors the functionality of the LangGraph-based system in `../agents/` but leverages ADK's orchestration primitives for better scalability and Google ecosystem integration.

## Overview

The system uses a hierarchical multi-agent architecture to detect, analyze, and respond to flight disruptions:

```
Predictive Agent
    ↓
[Disruption Detected?]
    ↓ Yes
Orchestrator Agent
    ↓
Parallel Sub-Agents:
    ├─ Risk Agent
    ├─ Rebooking Agent
    ├─ Finance Agent
    └─ Crew Agent
    ↓
Aggregator Agent
    ↓
Final Action Plan
```

## Architecture

### Key Components

1. **State Management** (`state.py`)
   - `DisruptionState`: Pydantic model for shared state
   - Audit logging for transparency
   - Structured data flow between agents

2. **Custom Tools** (`tools.py`)
   - `predictive_signal_tool`: Compute disruption risk from signals
   - `rebooking_tool`: Generate passenger re-accommodation plans
   - `finance_tool`: Calculate financial impact (EU261/HKCAD)
   - `crew_scheduling_tool`: Assess crew duty limits and availability

3. **Agents** (`agents.py`)
   - **PredictiveAgent**: Detects disruptions using weather/aircraft/crew signals
   - **OrchestratorAgent**: Creates action plans and what-if scenarios
   - **RiskAgent**: Assesses likelihood, duration, and regulatory impact
   - **RebookingAgent**: Plans passenger re-accommodation and hotel arrangements
   - **FinanceAgent**: Calculates compensation and operational costs
   - **CrewAgent**: Manages crew scheduling and compliance
   - **AggregatorAgent**: Synthesizes all outputs into final plan

4. **Workflow Orchestration** (`workflow.py`)
   - `DisruptionWorkflowADK`: Main workflow class
   - Sequential execution with conditional routing
   - Parallel sub-agent execution
   - Comprehensive error handling

## Google ADK Integration

### Current Implementation

The current implementation uses **ADK-compatible patterns** but runs standalone without requiring the full ADK package. This allows:
- Immediate testing and development
- Understanding of ADK concepts
- Easy migration to full ADK when ready

### Migration to Full ADK

To use the actual Google ADK, install:

```bash
pip install google-adk
```

Then update the agents to use real ADK primitives:

```python
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from google.adk.tools import Tool

# Example: Convert PredictiveAgent to ADK LlmAgent
predictive_agent = LlmAgent(
    name="predictive_agent",
    model="gemini-2.5-flash",
    instruction="Analyze flight signals and detect disruptions",
    tools=[predictive_signal_tool]
)

# Orchestrate with SequentialAgent
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

## Usage

### Running the Workflow

```python
from app.agentsv2 import DisruptionWorkflowADK

# Initialize workflow
workflow = DisruptionWorkflowADK()

# Execute with flight data
flight_data = {
    "airport": "HKG",
    "carrier": "CX",
    "stats": {
        "weatherScore": 0.7,
        "aircraftScore": 0.6,
        "crewScore": 0.5,
        "paxImpacted": 200
    },
    "flights": [...]
}

# Async execution
result = await workflow.run(flight_data)

# Synchronous execution
result = workflow.run_sync(flight_data)
```

### Output Structure

```python
{
    "final_plan": {
        "disruption_detected": true,
        "priority": "high",
        "recommended_action": "PROCEED",
        "risk_assessment": {...},
        "rebooking_plan": {...},
        "finance_estimate": {...},
        "crew_rotation": {...},
        "what_if_scenarios": [...]
    },
    "audit_log": [
        {
            "agent": "PredictiveAgent",
            "input": {...},
            "output": {...},
            "timestamp": "2024-01-01T12:00:00"
        },
        ...
    ],
    "disruption_detected": true,
    "risk_assessment": {...},
    "rebooking_plan": {...},
    "finance_estimate": {...},
    "crew_rotation": {...},
    "simulation_results": [...]
}
```

## Key Differences from LangGraph Implementation

| Aspect | LangGraph (`../agents/`) | ADK (`agentsv2/`) |
|--------|--------------------------|-------------------|
| **Framework** | LangGraph with StateGraph | Google ADK with Sequential/Parallel |
| **State** | TypedDict | Pydantic BaseModel |
| **Orchestration** | Graph nodes + edges | Agent hierarchy |
| **LLM Integration** | langchain-core | google.genai (Gemini) |
| **Parallelization** | Graph edges | ParallelAgent |
| **Tool System** | LangChain tools | ADK tools (async) |
| **Deployment** | Generic | Optimized for Vertex AI |

## Features

### ✅ Implemented
- Multi-agent hierarchical architecture
- Predictive disruption detection
- What-if scenario simulation
- Parallel agent execution
- Comprehensive audit logging
- VIP passenger prioritization
- EU261/HKCAD compliance calculations
- Crew duty time monitoring

### 🚧 Planned Enhancements
- Full Google ADK integration (LlmAgent, SequentialAgent, ParallelAgent)
- Gemini model integration via Vertex AI
- Real-time API integrations (Amadeus, Sabre, Expedia)
- Voice/chat interface via Dialogflow
- Vertex AI deployment
- Context caching for performance
- Evaluation framework integration

## Testing

### Unit Tests
```bash
# Test individual tools
pytest backend/app/agentsv2/tests/test_tools.py

# Test agents
pytest backend/app/agentsv2/tests/test_agents.py

# Test workflow
pytest backend/app/agentsv2/tests/test_workflow.py
```

### Integration Test
```bash
# Run with mock flight data
python -m app.agentsv2.test_integration
```

### Development Server
```bash
# Start backend with ADK workflow
./run_dev.sh
```

## Environment Variables

```bash
# Required for full ADK integration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True

# LLM configuration
LLM_PROVIDER=google  # or openai, anthropic
GOOGLE_API_KEY=your-api-key
```

## Dependencies

Current (standalone):
- `pydantic>=2.9.2`: State management
- `fastapi>=0.115.4`: API integration
- Standard library (asyncio, logging, etc.)

For full ADK:
```bash
pip install google-adk
pip install google-cloud-aiplatform
```

## Comparison with Original Design

This implementation follows the design outlined in `google_a2a_agents_apiV2.md`:

| Feature | Design Doc | Implementation |
|---------|------------|----------------|
| **Framework** | ADK | ✅ ADK-compatible patterns |
| **Agents** | LlmAgent hierarchy | ✅ Hierarchical agents |
| **Tools** | Custom + pre-built | ✅ Custom tools implemented |
| **Orchestration** | Sequential + Parallel | ✅ Workflow orchestration |
| **State** | Pydantic model | ✅ DisruptionState |
| **What-if** | Scenario simulation | ✅ Orchestrator generates scenarios |
| **MCP Dashboard** | Streamlit monitoring | 🚧 Planned |
| **Real APIs** | Amadeus, Expedia | 🚧 Planned |

## Contributing

When adding new agents or tools:

1. Define tools in `tools.py` as async functions
2. Create agent classes in `agents.py`
3. Update workflow orchestration in `workflow.py`
4. Add tests in `tests/`
5. Document in this README

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Python GitHub](https://github.com/google/adk-python)
- [Design Document](../../../google_a2a_agents_apiV2.md)
- [Original LangGraph Implementation](../agents/)

## License

Same as parent project.
