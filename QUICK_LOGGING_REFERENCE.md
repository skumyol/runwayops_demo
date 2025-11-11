# Quick Logging Reference

## See Agent Communication in Real-Time!

### Backend Logs (Terminal)

**Start the server:**
```bash
./run_dev.sh
```

**Then click "Enable AI" in the Agent Console. You'll see:**

```
================================================================================
🧠 PREDICTIVE AGENT: Starting disruption analysis...
================================================================================
📊 Input Data: 5 flights, Stats: {...}
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
✨ ORCHESTRATOR: LLM Response received (length: 1234 chars)
✅ ORCHESTRATOR: Decision: Intervention: True, Severity: high
📤 ORCHESTRATOR: Output generated - Generated 2 what-if scenarios
💬 ORCHESTRATOR → SUB-AGENTS: Dispatching tasks to Risk, Rebooking, Finance, and Crew agents
✅ ORCHESTRATOR AGENT: Execution SUCCESS
================================================================================
```

### Frontend Logs (Browser Console)

**Open DevTools:**
- Press `F12` (Windows/Linux)
- Press `Cmd+Option+I` (Mac)
- Right-click → "Inspect" → "Console" tab

**Then click "Enable AI". You'll see:**

```
🤖 AI Options Generation Started
  Flight: CX255
  Passenger: AA145J
  Time: 3:45:23 PM

✅ AI Options Generated
  ⏱️  Duration: 8.2s
  📊 Provider: deepseek/deepseek-chat
  🎯 Options: 3
  ⚠️  Disruption: DETECTED
  🛡️  Risk: high
  ✨ Action: PROCEED
  💯 Confidence: high
  
  (index) │ id          │ route         │ cabin │ seats │ score │ badges
  ───────────────────────────────────────────────────────────────────────
     0    │ agent-opt-1 │ HKG→SIN→LHR  │  Y    │  52   │  92   │ Fastest, Agent Recommended
     1    │ agent-opt-2 │ HKG→DXB→LHR  │  Y    │  78   │  85   │ More Seats
     2    │ agent-opt-3 │ HKG→LHR      │  J    │  32   │  95   │ Premium, Hotel Included
```

**Or for full analysis (click "View Full Agent Analysis"):**

```
🤖 Agent Analysis Started
  Flight: CX255
  Time: 3:45:23 PM

✅ Agent Analysis Complete
  ⏱️  Duration: 12.4s
  📊 Provider: deepseek/deepseek-chat
  🔢 Agents Executed: 7
  ⚠️  Disruption: DETECTED
  🎯 Final Plan: {...}
  
  📋 Agent Execution Flow:
    1. 🧠 Predictive: Analyzed 5 flights: 2 delayed, 1 critical...
    2. ✨ Orchestrator: Generated main plan with 2 scenarios...
    3. 🛡️ Risk: Likelihood: high, Duration: 3-5 hours...
    4. ✈️ Rebooking: Same-day alternative with premium protection...
    5. 💰 Finance: Total estimate: $45,000 (156 passengers)
    6. 👥 Crew: Changes needed: 2, Backup required: 1
    7. 📊 Aggregator: Action: PROCEED, Confidence: high
  
  💡 View full details in "View Agent Analysis" modal
```

## Quick Test

**1. Start Server:**
```bash
./run_dev.sh
```

**2. Open Browser:**
- Go to: http://localhost:3000
- Open DevTools (F12)
- Go to Console tab

**3. Trigger Agents:**
- Navigate to Agent Console
- Select flight CX255
- Click "Enable AI" button
- **Watch logs appear in BOTH terminal AND browser console!**

## Emoji Legend

- 🧠 Predictive Agent
- ✨ Orchestrator Agent  
- 🛡️ Risk Agent
- ✈️ Rebooking Agent
- 💰 Finance Agent
- 👥 Crew Agent
- 📊 Aggregator Agent
- 💬 Agent Communication
- 🔮 LLM API Call
- ✅ Success
- ❌ Error
- ⚠️ Warning

## That's It!

**Backend logs**: Real-time agent communication in your terminal  
**Frontend logs**: User-friendly summaries in browser console  

**Just open both and click "Enable AI" to see agents talking to each other!** 🚀
