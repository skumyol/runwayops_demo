# APIV2 Agentic System Blueprint

This blueprint re-implements the flight disruption agentic structure as **APIV2**. LangGraph continues to live as the fast, local orchestration surface for hackathon demos and regression tests, while the new `google_a2a_agents_apiV2` stack (Google Agent Development Kit + Vertex AI) becomes the production brain that can call real airline systems such as Amadeus. Use this document instead of the previous LangGraph-only write-up.

## Dual Runtime Strategy

| Concern | LangGraph Surface (v1) | `google_a2a_agents_apiV2` Surface (APIV2) |
| --- | --- | --- |
| Execution scope | On-demand runs inside `backend` or notebooks; perfect for quick AI analysis triggers | Long-running agent service (Vertex AI Agent Engine / Cloud Run) with retry + monitoring |
| Ownership | Remains source-of-truth for graph topology and guardrails | Hosts the intelligent hierarchy (Predictive → Orchestrator → Risk/Rebooking/Finance/Crew → Aggregator) |
| Primary LLM | OpenAI / Grok via `langchain_openai` | Gemini 1.5 Pro (temperature 0.2) with OpenAI/Grok fallbacks |
| Tooling | Existing Python functions, mock data, and LangGraph conditional edges | ADK `LlmAgent`, `Sequential`, `Parallel`, and custom tools (Amadeus, Hotel, Cost calculators) |
| Observability | MongoDB audit log + dashboard tab in Vite UI | Streamlit / Firestore-backed Mission Control Panel (MCP) with Firestore traces and Vertex logs |

**Key idea:** trigger evaluation still enters LangGraph first (cheap heuristics, deterministic gating). Once disruption probability > 70%, hand the state payload to APIV2 so Google ADK executes the richer workflow and emits structured plans back to FastAPI + Vite. This lets us iterate locally without blocking the higher-fidelity agent service.

## APIV2 Architecture Overview

```
Flight Monitor Streams (synthetic/realtime)
        │
        ▼
LangGraph Guardrail Graph (predictive check, throttle, legacy mocks)
        │ handoff via REST/gRPC (AgentState JSON)
        ▼
Google ADK Orchestrator (APIV2)
  ├─ Predictive Tool (TensorFlow Lite / heuristics)
  ├─ LlmAgent Orchestrator (Gemini)
  └─ Parallel Sub-Agents
       ├─ Risk Agent
       ├─ Rebooking Agent (Amadeus, Hotels)
       ├─ Finance Agent
       └─ Crew Agent
        │
        ▼
Aggregator + Audit Log Writer (Firestore/Mongo)
        │
        ├─ Mission Control Panel (Streamlit/WebSocket)
        └─ FastAPI `/api/disruption` + Vite dashboard
```

## Code Layout

- `backend/app/agentsv2/state.py` – typed `FlightAgentState` + audit logging helper shared by every ADK stage.
- `backend/app/agentsv2/tools.py` – deterministic Predictive, Scenario, Rebooking, Finance, Crew, and Aggregation tools that double as ADK registrations.
- `backend/app/agentsv2/agents.py` – ADK-aligned agents (Predictive, Gemini Orchestrator, Risk, Rebooking, Finance, Crew, Aggregator) that call the tool belt.
- `backend/app/agentsv2/workflow.py` – Sequential + Parallel composites that mimic Google ADK graph execution so FastAPI can invoke APIV2 just like the LangGraph runner.

## Implementation Steps (mirrors `google_a2a_agents_apiV2`)

### 1. Foundation and Environment
- Install ADK and friends: `uv pip install google-adk google-cloud-aiplatform streamlit pydantic requests` (backed by Step 1 in the Google plan).
- Keep `./run_dev.sh` as the unified dev entry point; it now boots the backend, Vite dashboard, *and* the APIV2 service (if `AGENTIC_MODE=apiv2`).
- Extend `.env`: `GEMINI_API_KEY`, `VERTEX_PROJECT_ID`, `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`, `FLIGHT_MONITOR_MODE=synthetic` by default.

### 2. Shared State and Graph Definition
Use ADK’s `TypedDict` state (same fields as `AgentState` in LangGraph) so both runtimes stay schema-compatible.

```python
# apiv2/workflow.py
from typing import TypedDict, List, Dict, Any
from datetime import datetime
from adk import LlmAgent, Sequential, Parallel

class FlightAgentState(TypedDict, total=False):
    input_data: Dict[str, Any]
    disruption_detected: bool
    risk_assessment: Dict[str, Any]
    rebooking_plan: Dict[str, Any]
    finance_estimate: Dict[str, Any]
    crew_rotation: Dict[str, Any]
    simulation_results: List[Dict[str, Any]]
    audit_log: List[Dict[str, Any]]
    final_plan: Dict[str, Any]

def log_trace(state: FlightAgentState, agent: str, payload: Dict[str, Any]) -> None:
    state.setdefault("audit_log", []).append({
        "agent": agent,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    })

predictive = LlmAgent.from_tool("predictive_signal_generator", model="gemini-1.5-pro")
bridge = Sequential([predictive])
sub_agents = Parallel([
    LlmAgent.from_tool("risk_agent"),
    LlmAgent.from_tool("rebooking_agent"),
    LlmAgent.from_tool("finance_agent"),
    LlmAgent.from_tool("crew_agent"),
])
workflow = Sequential([bridge, sub_agents, LlmAgent.from_tool("aggregator")])
```

- `predictive_signal_generator`, `risk_agent`, etc. can call the same Python code we previously wrapped with LangGraph tools. ADK simply gives us deployment hooks, Vertex scaling, and evaluation tooling.
- LangGraph still runs `disruption_workflow.py` for smoke tests. When the backend is started with `AGENTIC_MODE=langgraph`, requests never leave the original graph; switching the env flag pushes payloads to the APIV2 endpoint.

### 3. Tool Belt & External Systems
Derived from Step 3 in the Google plan and grounded with `amadeus_integration.md`:
- **Amadeus Connector** – reuse `amadeus_client.py` as the `RebookingTool`. Wrap it in an async ADK tool that can fetch offers, price them, and confirm bookings. Map results back into `rebooking_plan` (PNR, fare class, hotel fallback).
- **Hotel / Cost Tools** – optional HTTP tools (could hit Expedia Rapid API or static mocks initially).
- **Predictive + Crew Tools** – run existing heuristics (signal scoring, crew legality) using ADK’s Code Execution tool so Gemini orchestrator can retrieve hard numbers.

### 4. Observability & Mission Control
- Mirror Step 4 from the Google plan: push each `audit_log` entry to Firestore (or Mongo) and stream highlights over WebSocket to the MCP.
- The MCP described in `amadeus_integration.md` stays the canonical UI; the only change is that updates now include `plan.explainability` and Vertex trace IDs so ops can click from dashboard → Vertex console if needed.
- Keep LangGraph’s JSON log writer around for debugging; APIV2 just appends more metadata (LLM model, tool latency).

### 5. Testing & Deployment
- Unit test each tool (pytest + pytest-asyncio). Mock Amadeus responses so test suite runs offline.
- Integration test: call `/api/disruption` twice, once with `AGENTIC_MODE=langgraph`, once with `apiv2`, and assert both return compatible schemas.
- Deployment: containerize `apiv2/workflow.py` with the FastAPI app, or deploy it separately on Vertex AI (recommended for scale). The Google plan estimates $0.10–0.50 per run; keep budgets in line by turning on `FLIGHT_MONITOR_MODE=synthetic` during dev.

## Making It Realistic with Amadeus (based on `amadeus_integration.md`)

The FastAPI sample in `amadeus_integration.md` already demonstrates how to stitch a real Amadeus booking loop into the mission control workflow. To align it with APIV2:

1. **`amadeus_client.py`** – keep exactly as written. Register its async methods as ADK tools so the Rebooking agent can fetch offers and confirm bookings without leaving the APIV2 graph.
2. **`workflow_runner.py`** – expose both runtimes:
   ```python
   async def run_disruption_workflow(payload: dict) -> dict:
       if settings.agentic_mode == "langgraph":
           return await langgraph_runner(payload)
       return await apiv2_runner(payload)  # wraps the ADK workflow above
   ```
3. **`main.py`** – the `/api/disruption` handler from the example now:
   - Invokes `run_disruption_workflow`
   - If the returned plan includes `rebooking_plan.requires_booking`, call `amadeus.search_alternatives()` then `amadeus.confirm_and_book()`
   - Broadcast the enriched plan (PNR, new flight number) over the MCP WebSocket
4. **`templates/mcp.html`** – keep the neon status view but add placeholders for APIV2 metadata (model, what-if branches, escalation status). The WebSocket payload already contains `plan` and `audit_log_length`; extend it with `plan.vertex_trace_url` for quick debugging.
5. **Deployment** – reuse the Dockerfile + Cloud Run instructions from `amadeus_integration.md`. APIV2 simply adds another container or Vertex endpoint—no changes needed for the dashboard or FastAPI beyond a new env var and HTTP client.

## Migration & Rollout Checklist

1. ✅ Copy this doc into your planning ritual; archive the old LangGraph-only walkthrough.
2. 🧪 Implement feature flags (`AGENTIC_MODE`) and run the dual-mode integration test.
3. 🧰 Register Amadeus + Hotel + Cost tools inside ADK, mirroring the Google plan’s Step 3 deliverables.
4. 📊 Stream APIV2 audit logs to both Mongo (legacy) and Firestore (new) until Vertex logger is battle-tested.
5. 🚀 Deploy APIV2 on Vertex AI Agent Engine; point FastAPI to the new endpoint in staging, then prod.

## References
- `google_a2a_agents_apiV2` – detailed ADK migration plan (sections 1–5 referenced throughout).
- `amadeus_integration.md` – FastAPI + MCP example that grounds the APIV2 output in real bookings.
- `AGENTIC_INTEGRATION.md` – still valid for understanding the legacy LangGraph graph; use it for fallback mode docs.
