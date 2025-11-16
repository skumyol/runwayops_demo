# ADK-Based Flight Disruption Management System

This directory contains the ADK-oriented version of the Cathay disruption workflow. It mirrors the LangGraph pipeline in `../agents/` but keeps the surface area small so we can later plug in Google's Agent Development Kit without re-doing business logic.

## Purpose
- Demonstrate how the existing disruption logic maps to ADK concepts (state, tools, agent orchestration).
- Provide a drop-in workflow (`DisruptionWorkflowADK`) the FastAPI app can toggle through `AGENTIC_ENABLED`.
- Document only the deltas from the LangGraph implementation so contributors are not reading two competing playbooks.

## Quick start
```bash
cd backend
uv pip install -r requirements.txt  # or python -m venv .venv && source .venv/bin/activate
```

```python
from app.agentsv2 import DisruptionWorkflowADK

workflow = DisruptionWorkflowADK()
result = await workflow.run(sample_flight_data)  # plan + per-agent decision traces
```

`python -m app.agentsv2.test_integration` runs the full workflow with the mock payload that powers the dashboard so you can see expected logs and outputs.

## Key modules
- `state.py` – Pydantic `DisruptionState`, audit helpers, decision logs.
- `tools.py` – async utilities for disruption scoring, rebooking, finance, and crew.
- `agents.py` – Predictive, Orchestrator, Risk, Rebooking, Finance, Crew, and Aggregator agents.
- `workflow.py` – `DisruptionWorkflowADK` plus sequential/parallel routing glue.

## Configuration
| Variable | Notes |
| --- | --- |
| `AGENTIC_ENABLED` | Switches FastAPI routes to use the v2 workflow. |
| `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE` | Point agents at OpenAI, OpenRouter, Gemini, etc. |
| Provider keys (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, …) | Needed only when calling hosted models. |
| `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` | Required once the real ADK SDK + Vertex AI path is enabled. |

LLM config is optional; without it the workflow falls back to deterministic heuristics so local testing still succeeds.

## Testing
```bash
pytest backend/app/agentsv2/tests/test_tools.py
pytest backend/app/agentsv2/tests/test_agents.py
pytest backend/app/agentsv2/tests/test_workflow.py
python -m app.agentsv2.test_integration
```

## Roadmap
- Replace the shims with the official `google-adk` package when it becomes available internally.
- Wire Gemini via Vertex AI (with caching) to keep sequential orchestration under SLA.
- Expand decision logging so `/api/v2/agents/analyze` returns the structured per-agent trace directly.
- Add regression tests covering live data feeds (Amadeus, Sabre, Expedia) once credentials are cleared.

## References
- [Google ADK docs](https://google.github.io/adk-docs/)
- [ADK Python repo](https://github.com/google/adk-python)
- [Design brief](../../../google_a2a_agents_apiV2.md)
- [LangGraph baseline](../agents/)
