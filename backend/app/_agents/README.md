# LangGraph Agents Module

This module contains the LangGraph-based multi-agent workflow for flight disruption analysis.

## Quick Start

```python
from app.agents import DisruptionWorkflow

# Initialize workflow
workflow = DisruptionWorkflow()

# Run analysis (async)
result = await workflow.run(flight_monitor_data)

# Or use sync version
result = workflow.run_sync(flight_monitor_data)

# Access results
print(result["final_plan"])
print(result["audit_log"])
```

## Module Structure

- **`state.py`**: Defines `AgentState` TypedDict shared across all nodes
- **`nodes.py`**: Individual agent implementations (predictive, orchestrator, sub-agents, aggregator)
- **`workflow.py`**: LangGraph state graph construction and execution
- **`__init__.py`**: Public exports

## Workflow Execution Flow

1. **Predictive Node** → Analyzes input, detects disruption
2. **Conditional Router** → Routes to orchestrator if detected, else END
3. **Orchestrator Node** → LLM generates main plan + what-if scenarios
4. **Parallel Sub-Agents** → Risk, Rebooking, Finance, Crew run concurrently
5. **Aggregator Node** → Combines all outputs into final plan
6. **END** → Returns complete state with audit log

## Agent Responsibilities

| Agent | Type | Input | Output |
|-------|------|-------|--------|
| Predictive | Heuristic/ML | Flight data | Risk probability, detection flag |
| Orchestrator | LLM (GPT-4o) | Risk + flight data | Main plan, what-if scenarios |
| Risk | LLM | Risk data | Likelihood, duration, impact, regulatory |
| Rebooking | LLM | Flight data | Strategy, hotel, VIP, pax count |
| Finance | LLM | Risk + rebooking | Costs (compensation, hotel, ops, total) |
| Crew | LLM | Flight data | Crew changes, backup needs, compliance |
| Aggregator | Logic | All agent outputs | Final synthesized plan |

## Configuration

Agents use settings from `app.config.Settings`:
- `agentic_enabled`: Master switch
- `openai_api_key`: LLM API key
- `llm_model`: Model name (default: gpt-4o)
- `llm_temperature`: Sampling temperature (default: 0.2)

## Extending

### Add a new agent node:

```python
# In nodes.py
def my_agent_node(state: AgentState) -> AgentState:
    llm = get_llm()
    # ... your logic
    result = {...}
    state = log_reasoning(state, "MyAgent", input_data, result)
    state["my_field"] = result
    return state
```

### Wire into graph:

```python
# In workflow.py
graph.add_node("my_agent", my_agent_node)
graph.add_edge("orchestrator", "my_agent")
graph.add_edge("my_agent", "aggregator")
```

### Update state definition:

```python
# In state.py
class AgentState(TypedDict):
    # ... existing
    my_field: Dict[str, Any]
```

## Error Handling

All LLM agents have fallback logic if JSON parsing fails:
- Returns generic structured output
- Logs raw LLM response for debugging
- Workflow continues (graceful degradation)

## Testing

```python
# Mock input
test_input = {
    "airport": "HKG",
    "carrier": "CX",
    "stats": {"totalFlights": 10, "delayed": 3, "critical": 1},
    "flights": [...]
}

# Run workflow
workflow = DisruptionWorkflow()
result = workflow.run_sync(test_input)

# Assertions
assert result["disruption_detected"] is True
assert len(result["audit_log"]) > 5
assert "final_plan" in result
```

## Performance

- **Avg execution time**: 5-15 seconds (depends on LLM latency)
- **Sub-agents run in parallel**: LangGraph handles concurrency
- **Cost per run**: ~$0.10-0.30 (GPT-4o, 5-6 LLM calls)

## Production Notes

- Replace predictive heuristics with trained ML model
- Consider caching/rate-limiting for cost control
- Monitor LLM output quality and add structured output mode if needed
- Audit logs stored in MongoDB via `services.agentic`
