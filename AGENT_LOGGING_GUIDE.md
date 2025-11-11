# Agent Communication Logging Guide

## Backend Logs

When AI agents run, you'll see detailed logs in the **backend terminal** showing agent-to-agent communication:

### Example Backend Logs:

```
================================================================================
🧠 PREDICTIVE AGENT: Starting disruption analysis...
================================================================================
📊 Input Data: 5 flights, Stats: {'totalFlights': 5, 'delayed': 2, 'critical': 1}
📈 Analysis: Total=5, Delayed=2, Critical=1, AvgDelay=45min
🎯 Risk Probability: 75.00% (threshold: 70%)
⚠️  Disruption DETECTED ✓
✅ PREDICTIVE AGENT: Execution SUCCESS
================================================================================

================================================================================
🤖 ORCHESTRATOR AGENT: Starting execution...
📥 Input: Coordinating response based on disruption: True
================================================================================
💭 ORCHESTRATOR: Analyzing risk assessment: high
💬 PREDICTIVE → ORCHESTRATOR: Disruption detected: True
🔮 ORCHESTRATOR: Calling LLM (deepseek-chat)...
   Prompt: You are an airline operations orchestrator...
✨ ORCHESTRATOR: LLM Response received
   (length: 1234 chars)
✅ ORCHESTRATOR: Decision: Intervention: True, Severity: high
📤 ORCHESTRATOR: Output generated
   Generated 2 what-if scenarios
💬 ORCHESTRATOR → SUB-AGENTS: Dispatching tasks to Risk, Rebooking, Finance, and Crew agents
✅ ORCHESTRATOR AGENT: Execution SUCCESS
================================================================================

[Similar detailed logs for Risk, Rebooking, Finance, Crew, and Aggregator agents...]
```

## Frontend Console Logs

The frontend automatically logs agent activity to the browser console when you enable AI options or run analysis.

### How to View Frontend Logs:

1. **Open Browser DevTools**: Press `F12` or `Cmd+Option+I` (Mac)
2. **Go to Console tab**
3. **Click "Enable AI" or "Get AI Suggestions"**
4. **Watch the logs appear in real-time**

### Example Frontend Console Output:

```javascript
🤖 Agent Analysis Started
────────────────────────────
Flight: CX255
Provider: deepseek
Model: deepseek-chat

✅ Agent Analysis Complete
────────────────────────────
Duration: 12.4 seconds
Agents Executed: 7
Disruption Detected: true
Risk Level: high
Recommended Action: PROCEED

📋 Agent Execution Flow:
  1. 🧠 Predictive → Disruption: DETECTED (85% probability)
  2. ✨ Orchestrator → Created 2 scenarios, Severity: high
  3. 🛡️ Risk → Likelihood: high, Duration: 3-5hrs
  4. ✈️ Rebooking → Strategy: Premium protection, 156 pax
  5. 💰 Finance → Cost: $45,000 (compensation + hotels)
  6. 👥 Crew → Changes needed: 2, Backup: 1
  7. 📊 Aggregator → Final: PROCEED, Confidence: high

💡 View full details in "View Agent Analysis" modal
```

## Log Emoji Guide

### Agent Types:
- 🧠 **Predictive** - ML-based disruption detection
- ✨ **Orchestrator** - Main coordinator, creates plan
- 🛡️ **Risk** - Assesses probability and impact
- ✈️ **Rebooking** - Plans passenger re-accommodation
- 💰 **Finance** - Estimates costs
- 👥 **Crew** - Handles crew rotation
- 📊 **Aggregator** - Combines all inputs into final recommendation

### Log Types:
- 📥 **Input** - Agent receiving data
- 📤 **Output** - Agent producing result
- 💭 **Thinking** - Agent reasoning process
- 🔮 **LLM Call** - Calling language model
- ✨ **LLM Response** - Received LLM response
- ✅ **Decision** - Agent made a decision
- 💬 **Communication** - Agent-to-agent message
- 📊 **Data** - Structured data
- ⚠️ **Warning** - Important notice
- ❌ **Error** - Something went wrong

## Viewing Logs

### Backend Logs (Terminal):

```bash
# Start dev server
./run_dev.sh

# Watch logs in terminal as agents execute
# You'll see real-time agent communication
```

### Frontend Logs (Browser):

```javascript
// Open DevTools Console (F12)
// Enable AI options or run analysis
// Logs appear automatically

// You can also manually inspect:
console.log(agentAnalysis)  // Full analysis object
console.log(agentAnalysis.analysis.audit_log)  // Detailed audit trail
```

## Debugging Tips

### 1. Backend Not Showing Logs?

Check that `AGENTIC_ENABLED=true` in `backend/.env` and restart:

```bash
# Verify setting
cat backend/.env | grep AGENTIC

# Should show:
# AGENTIC_ENABLED=true

# Restart to apply
./run_dev.sh
```

### 2. Want More Detailed Logs?

Edit `backend/app/agents/agent_logger.py` to increase verbosity:

```python
# Add more detailed logging
logger.setLevel(logging.DEBUG)  # Was INFO
```

### 3. Frontend Not Showing Logs?

Check browser console for errors:
- Make sure DevTools is open before clicking "Enable AI"
- Check Network tab for API responses
- Verify `AGENTIC_ENABLED=true` on backend

### 4. Export Logs for Analysis

Backend logs can be redirected to a file:

```bash
./run_dev.sh 2>&1 | tee agent_logs.txt
```

Frontend logs can be copied from console:
- Right-click in console → "Save as..."
- Or copy-paste individual log entries

## Log Format Examples

### Successful Agent Execution:

```
✅ RISK AGENT: Decision: Likelihood: high
   Rationale: Based on delay patterns and weather data
📤 RISK: Output generated
   likelihood=high, duration=3-5hrs, impact=156 pax
💬 RISK → AGGREGATOR: Risk assessment complete
✅ RISK AGENT: Execution SUCCESS
```

### Agent Error Handling:

```
❌ ORCHESTRATOR: LLM parsing error: Invalid JSON
⚠️  ORCHESTRATOR: Falling back to automated plan
✅ ORCHESTRATOR AGENT: Execution SUCCESS (fallback mode)
```

### Agent Communication Chain:

```
💬 PREDICTIVE → ORCHESTRATOR: Disruption detected: True
💬 ORCHESTRATOR → SUB-AGENTS: Dispatching tasks...
💬 RISK → AGGREGATOR: Risk assessment complete
💬 REBOOKING → AGGREGATOR: Strategy ready
💬 FINANCE → AGGREGATOR: Cost estimate ready
💬 CREW → AGGREGATOR: Crew plan ready
💬 AGGREGATOR → USER: Final recommendation ready
```

## Integration with Frontend

### AgentAuditTrail Component

The `AgentAuditTrail` component automatically displays agent logs in a beautiful UI:

```tsx
<AgentAuditTrail
  auditLog={analysis.analysis?.audit_log || []}
  finalPlan={analysis.analysis?.final_plan}
  metadata={analysis.metadata}
/>
```

Features:
- ✅ Expandable agent cards
- ✅ Color-coded by agent type
- ✅ Reasoning transparency
- ✅ Raw data access
- ✅ Timeline view

### Custom Console Logging

Add custom logging in your components:

```typescript
// In useAgentOptions.ts or useAgentReaccommodation.ts
console.group('🤖 Agent Analysis Started');
console.log('Flight:', flightNumber);
console.log('Provider:', provider);
console.groupEnd();

// After analysis
console.group('✅ Agent Analysis Complete');
console.table(audit_log);  // Table format
console.groupEnd();
```

## Performance Monitoring

Track agent execution time:

```javascript
// Backend logs show timestamps
INFO: 15:23:01 - PREDICTIVE AGENT: Starting...
INFO: 15:23:02 - PREDICTIVE AGENT: Complete (1.2s)

// Frontend can measure total time
const start = performance.now();
await analyzeFlightWithAgents(flight);
const duration = ((performance.now() - start) / 1000).toFixed(1);
console.log(`⏱️ Total Duration: ${duration}s`);
```

## Summary

**Backend Logs**: Detailed agent-to-agent communication in terminal  
**Frontend Logs**: User-friendly summaries in browser console  
**Agent Audit Trail**: Beautiful UI component showing full execution flow  
**Real-time**: See agents communicate as they work  
**Transparent**: Every decision explained with reasoning  

**Open your terminal and browser console to see agents in action!** 🚀
