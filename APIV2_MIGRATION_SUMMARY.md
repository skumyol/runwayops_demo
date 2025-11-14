# APIV2 (ADK) Migration & Enhanced Logging Summary

## ✅ Changes Completed

### 1. Removed LangGraph, Using Only APIV2 (ADK)

**Backend Changes:**
- Updated `/Users/skumyol/Documents/GitHub/runwayops_demo/backend/app/services/agentic.py`
  - Removed LangGraph import and references
  - Now only uses `APIV2Workflow` from `agentsv2` module
  - Updated type hints to only support `EngineName = Literal["apiv2"]`
  
- Updated `/Users/skumyol/Documents/GitHub/runwayops_demo/backend/app/config.py`
  - Changed `AGENTIC_ENGINES = {"apiv2"}` (removed "langgraph")
  - Default engine is now `apiv2` only

- Updated `/Users/skumyol/Documents/GitHub/runwayops_demo/backend/app/routes/agent_options.py`
  - Updated documentation to reference APIV2 (ADK) instead of LangGraph
  - Query parameter description now says "only 'apiv2' supported"

- Fixed import paths in routes:
  - `/Users/skumyol/Documents/GitHub/runwayops_demo/backend/app/routes/agentic.py`
  - `/Users/skumyol/Documents/GitHub/runwayops_demo/backend/app/routes/agent_options.py`
  - `/Users/skumyol/Documents/GitHub/runwayops_demo/backend/app/routes/agent_reaccommodation.py`
  - Changed `from ..agents` to `from .._agents` for llm_factory imports

**Frontend Changes:**
- Updated `/Users/skumyol/Documents/GitHub/runwayops_demo/frontend/dashboard/src/views/AgentPassengerPanel.tsx`
  - Changed "LangGraph agents" to "APIV2 (ADK) agents"
  - Updated modal title from "Complete LangGraph workflow" to "Complete APIV2 (ADK) workflow"

### 2. Enhanced Backend Logging

**Added comprehensive logging to:**

#### a) Agent Options Route (`agent_options.py`)
```python
logger.info("=" * 80)
logger.info(f"🤖 AGENT OPTIONS REQUEST: {flight_number}")
logger.info(f"   Engine: {engine or 'default'}")
logger.info(f"   Provider: {settings.llm_provider} / {settings.llm_model}")
logger.info("=" * 80)

logger.info("📊 Step 1: Fetching flight data")
logger.info(f"✅ Found flight manifest: {manifest.summary.affectedCount} affected passengers")

logger.info("📊 Step 2: Fetching passengers and crew data")
logger.info(f"✅ Retrieved: {len(passengers_raw)} passengers, {len(crew_raw)} crew members")
logger.info(f"⚠️  Disruption: {disruption.disruptionType} - {disruption.reason}")

logger.info("🚀 Step 3: Launching agent workflow")
logger.info("-" * 80)
# Agent workflow runs here
logger.info("-" * 80)
logger.info("✅ Agent workflow completed")

# Log agent decisions
logger.info("📋 AGENT DECISIONS:")
logger.info(f"   Priority: {plan.get('priority')}")
logger.info(f"   Confidence: {plan.get('confidence')}")
logger.info(f"   Finance Impact: ${finance.get('total_usd'):,.0f}")
logger.info(f"   Rebooking Strategy: {rebooking.get('strategy')}")

logger.info("🎯 Step 4: Converting agent analysis to UI options")
logger.info(f"✅ Generated {len(agent_options)} reaccommodation options")
```

#### b) Agentic Service (`services/agentic.py`)
```python
logger.info(f"🔧 AgenticService: Using engine '{engine_name}'")
logger.info(f"   Flight: {flight_data.get('flight_number')}")
logger.info(f"   Stats: {flight_data.get('stats')}")
logger.info(f"🏃 AgenticService: Running {engine_name} workflow...")
logger.info(f"✅ AgenticService: Workflow complete, persisting results...")
logger.info(f"🔧 Initialized APIV2 (ADK) workflow instance")
```

#### c) APIV2 Workflow (`agentsv2/workflow.py`)
The APIV2 workflow already has comprehensive logging:
```python
logger.info("=" * 80)
logger.info("🚀 Starting ADK Disruption Workflow")
logger.info("=" * 80)

logger.info("✓ No disruption detected - workflow complete")
logger.info("⚠️  Disruption detected - proceeding with orchestration")
logger.info("🔄 Running parallel sub-agents...")
logger.info("✅ Parallel sub-agents complete")

logger.info("=" * 80)
logger.info("✅ ADK Disruption Workflow Complete")
logger.info("=" * 80)
```

### 3. Frontend Console Logging

**Already exists in** `useAgentOptions.ts`:
```javascript
console.group('🤖 AI Options Generation Started');
console.log('Flight:', flightNumber);
console.log('Time:', new Date().toLocaleTimeString());

console.group('✅ AI Options Generated');
console.log(`⏱️  Duration: ${duration}s`);
console.log(`📊 Provider: ${result.provider}/${result.model}`);
console.log(`🎯 Options: ${result.options?.length || 0}`);
console.log(`⚠️  Disruption: ${result.analysis_summary.disruption_detected}`);
console.table(result.options);
```

## How to See Agent Communications

### Backend Terminal Logs

When you click "Enable AI" in the Agent Console, you'll see detailed logs:

```
================================================================================
🤖 AGENT OPTIONS REQUEST: CX255
   Engine: default (apiv2)
   Provider: openai / gpt-4o
================================================================================
📊 Step 1: Fetching flight data for CX255
✅ Found flight manifest: 156 affected passengers
📊 Step 2: Fetching passengers and crew data
✅ Retrieved: 156 passengers, 12 crew members
⚠️  Disruption: mechanical - Inbound aircraft requiring maintenance clearance
🚀 Step 3: Launching agent workflow
--------------------------------------------------------------------------------
🔧 AgenticService: Using engine 'apiv2'
   Flight: CX255
   Stats: {'totalPassengers': 156, 'totalCrew': 12, 'affectedCount': 156}
🏃 AgenticService: Running apiv2 workflow...
================================================================================
🚀 Starting ADK Disruption Workflow
================================================================================
⚠️  Disruption detected - proceeding with orchestration
🔄 Running parallel sub-agents...
✅ Parallel sub-agents complete
================================================================================
✅ ADK Disruption Workflow Complete
================================================================================
✅ AgenticService: Workflow complete, persisting results...
--------------------------------------------------------------------------------
✅ Agent workflow completed
📋 AGENT DECISIONS:
   Priority: high
   Confidence: high
   Finance Impact: $142,000
   Rebooking Strategy: immediate_alternative
   Affected Pax: 156
   Actions: 5
🎯 Step 4: Converting agent analysis to UI options
✅ Generated 3 reaccommodation options
```

### Frontend Browser Console

Open Developer Tools → Console tab to see:

```
🤖 AI Options Generation Started
  Flight: CX255
  Passenger: AA145J
  Time: 12:30:45

✅ AI Options Generated
  ⏱️  Duration: 3.2s
  📊 Provider: openai/gpt-4o
  🎯 Options: 3
  ⚠️  Disruption: DETECTED
  🛡️  Risk: high
  ✨ Action: IMMEDIATE_REACCOMMODATION
  💯 Confidence: high

[Options Table Display]
id               route            cabin  seats  score  badges
agent-opt-1      HKG → SIN → LHR  Y      50     92     Fastest, Agent Recommended
agent-opt-2      HKG → DXB → LHR  Y      75     85     More Seats
agent-opt-3      HKG → LHR        J      40     95     Premium, Hotel Included
```

## Current System Architecture

### Single Agent System: APIV2 (ADK)

**What it does:**
- Multi-agent orchestration using Google Agent Development Kit (ADK)
- Predictive Agent → Orchestrator → Parallel(Risk, Rebooking, Finance, Crew) → Aggregator
- Generates reaccommodation options with "WHY" reasoning
- Provides finance estimates and rebooking strategies

**Where it's used:**
1. **Agent Console** → "Enable AI" button
2. **IOC Dashboard** → "Run AI Analysis" button  
3. **Realtime Monitor** → "AI Analysis" tab

**Model/Provider:**
- Configured via environment variables
- Defaults: `openai` / `gpt-4o`
- Can be changed to DeepSeek, Gemini, OpenRouter

## Testing the Enhanced Logs

### Steps to Test:

1. **Start the development server:**
   ```bash
   ./run_dev.sh
   ```

2. **Open http://localhost:3000**

3. **Navigate to Agent Console** (top navigation)

4. **Select a flight** (e.g., CX255)

5. **Select a passenger**

6. **Click "Enable AI"** button

7. **Watch the backend terminal** for detailed logs showing:
   - Request initiation
   - Data fetching steps
   - Agent workflow execution
   - Decision details
   - Options generation

8. **Open browser console** (F12 → Console tab) to see:
   - Timing information
   - Provider/model info
   - Options generated
   - Risk assessment
   - Pretty-printed tables

## Files Modified

### Backend
- ✅ `backend/app/services/agentic.py` - Removed LangGraph, enhanced logging
- ✅ `backend/app/config.py` - Updated AGENTIC_ENGINES
- ✅ `backend/app/routes/agent_options.py` - Added comprehensive logging
- ✅ `backend/app/routes/agentic.py` - Fixed imports
- ✅ `backend/app/routes/agent_reaccommodation.py` - Fixed imports

### Frontend
- ✅ `frontend/dashboard/src/views/AgentPassengerPanel.tsx` - Updated UI text
- ✅ `frontend/dashboard/src/hooks/useAgentOptions.ts` - Already has console logging

## Environment Variables

To enable the agentic system, ensure these are set in `backend/.env`:

```bash
AGENTIC_ENABLED=true
AGENTIC_MODE=apiv2
LLM_PROVIDER=openai  # or deepseek, gemini, openrouter
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.2
OPENAI_API_KEY=your_key_here
```

## Next Steps (Optional)

1. **Add more detailed agent-to-agent communication logs** in individual agent classes
2. **Create log visualization UI** to show agent decision tree
3. **Add performance metrics** (timing for each agent)
4. **Export logs** to file for debugging
5. **Add log filtering** by level/component
