# Agent Details in Re-accommodation Console

## What You'll See Now

### 1. **AI Suggestions Button** (Right Sidebar)
Click "Get AI Suggestions" to get quick recommendations.

### 2. **NEW: View Full Agent Analysis Button**
After AI suggestions appear, you'll see a new button:
```
📄 View Full Agent Analysis
```

## How to View Agent Details

### Step 1: Get AI Suggestions
1. Select a flight from dropdown
2. Select a passenger (optional)
3. Click **"Get AI Suggestions"** (purple button)
4. Wait 5-15 seconds for analysis

### Step 2: View Detailed Agent Flow
After suggestions appear, click **"View Full Agent Analysis"**

## What You'll See in Agent Details Modal

### 🤖 Agent Execution Flow

A beautiful modal showing the complete LangGraph workflow:

```
┌─────────────────────────────────────────┐
│  Agent Execution Details                │
│  Complete LangGraph workflow for CX255  │
├─────────────────────────────────────────┤
│                                         │
│  [Step 1] 🧠 Predictive Agent          │
│  ├─ Disruption Detected: ✓             │
│  ├─ Risk Probability: 85%              │
│  └─ View Raw Data ▼                    │
│                                         │
│  [Step 2] ✨ Orchestrator Agent        │
│  ├─ Main Plan: Same-day alternative... │
│  ├─ Scenarios: delay_3hr, crew_short   │
│  └─ View Raw Data ▼                    │
│                                         │
│  [Step 3] 🛡️ Risk Agent                │
│  ├─ Likelihood: high                   │
│  ├─ Duration: 3-5 hours                │
│  ├─ Impact: 156 passengers             │
│  └─ Reasoning: High probability...     │
│                                         │
│  [Step 4] ✈️ Rebooking Agent           │
│  ├─ Strategy: Premium protection...    │
│  ├─ Affected: 156 passengers           │
│  └─ Reasoning: Priority for Gold...    │
│                                         │
│  [Step 5] 💰 Finance Agent             │
│  ├─ Compensation: $25,000              │
│  ├─ Hotel & Meals: $15,000             │
│  ├─ Total: $45,000                     │
│  └─ Reasoning: Based on EU261...       │
│                                         │
│  [Step 6] 👥 Crew Agent                │
│  ├─ Changes Needed: 2                  │
│  ├─ Backup Required: 1                 │
│  └─ Reasoning: Duty time limits...     │
│                                         │
│  [Step 7] 📊 Aggregator                │
│  ├─ Action: PROCEED                    │
│  ├─ Confidence: high                   │
│  ├─ Priority: critical                 │
│  └─ View Raw Data ▼                    │
│                                         │
│  ════════════════════════════════════  │
│                                         │
│  ✓ Final Recommendation                │
│  Action: PROCEED | Priority: critical  │
│  Confidence: high | Risk: high         │
│                                         │
│  Provider: deepseek • Model: deepseek-chat │
│  Analysis completed at 3:15:23 PM      │
│                                         │
├─────────────────────────────────────────┤
│  [Close]  [🔄 Re-run Analysis]         │
└─────────────────────────────────────────┘
```

## Features of Agent Details View

### For Each Agent Step:

**1. Expandable Cards**
- Click any agent card to expand/collapse
- See color-coded agents (purple, indigo, red, blue, green, orange, teal)
- Each has a unique icon (Brain, Sparkles, Shield, Plane, Dollar, Users, TrendingUp)

**2. Structured Output**
- Key metrics displayed clearly
- Badges for important values (priority, confidence, risk level)
- Easy-to-read formatting

**3. Reasoning Transparency**
- Each agent explains its thinking
- See WHY recommendations were made
- Full context for every decision

**4. Raw Data Access**
- "View Raw Data" dropdown for each agent
- JSON output for technical debugging
- Complete input/output trace

**5. Timeline View**
- Timestamp for each agent execution
- Step numbers (1-7)
- Sequential flow visualization

### Modal Actions:

**Close Button**
- Exit modal, return to main console

**Re-run Analysis Button**
- Force fresh analysis (bypasses cache)
- Useful if situation changed
- Takes 5-15 seconds

## Use Cases

### 1. **Understand AI Decisions**
- "Why did it prioritize Diamond passengers?"
- → Check Rebooking Agent reasoning

### 2. **Verify Cost Estimates**
- "How was $45,000 calculated?"
- → Check Finance Agent breakdown

### 3. **Debug Issues**
- "Why wasn't disruption detected?"
- → Check Predictive Agent output

### 4. **Audit Compliance**
- Complete trail of all agent decisions
- Timestamps for regulatory reporting
- Immutable log stored in MongoDB

### 5. **Training & Learning**
- Show new agents how AI analyzes disruptions
- Understand multi-agent orchestration
- See real-world LangGraph workflow

## Technical Details

### Data Flow:
```
Button Click
    ↓
POST /api/agent-reaccommodation/analyze/{flight}
    ↓
LangGraph Workflow Executes:
  • Predictive → detect disruption
  • Orchestrator → create plan + scenarios
  • [Risk, Rebooking, Finance, Crew] → parallel analysis
  • Aggregator → combine outputs
    ↓
Return: { analysis, metadata }
    ↓
Display in AgentAuditTrail component
```

### Components:
- **AgentAuditTrail.tsx** - Main visualization component
- **AgentPassengerPanel.tsx** - Hosts modal
- **useAgentReaccommodation.ts** - API hook

### Backend Endpoint:
```bash
POST /api/agent-reaccommodation/analyze/CX255
```

Returns complete audit log with all agent inputs/outputs.

## Tips

1. **First Time**: Click "Get AI Suggestions" before "View Full Agent Analysis"
2. **Faster**: Suggestions endpoint is faster (simplified output)
3. **Detailed**: Full analysis has complete reasoning and raw data
4. **Expand All**: Use button at top to expand all agents at once
5. **Re-run**: Use to get fresh analysis after situation changes

## Comparison

| Feature | Get AI Suggestions | View Full Agent Analysis |
|---------|-------------------|-------------------------|
| **Speed** | 5-10 sec | 5-15 sec |
| **Output** | Simplified | Complete audit trail |
| **Details** | Summary only | All agent reasoning |
| **UI** | Inline card | Full-screen modal |
| **Use Case** | Quick check | Deep investigation |
| **Cost** | ~$0.004 | ~$0.004 (same) |

## Screenshots of Agent Cards

### Predictive Agent
```
🧠 Predictive Agent                [Step 1]
⏰ 3:15:01 PM

✓ Disruption Detected
Risk Probability: 85%

Reasoning: Based on delay patterns and 
weather data, high likelihood of extended 
disruption affecting 156 passengers...

[View Raw Data ▼]
```

### Finance Agent
```
💰 Finance Agent                   [Step 5]
⏰ 3:15:08 PM

Compensation:        $25,000
Hotel & Meals:       $15,000
Operational Cost:     $5,000
─────────────────────────────
Total:               $45,000

Reasoning: EU261 regulations require €600
per passenger for delays >4hrs. Hotel costs
estimated at $95/night for 156 pax...

[View Raw Data ▼]
```

## Troubleshooting

### Modal doesn't appear
- Ensure you clicked the button after AI suggestions loaded
- Check browser console for errors

### No agent data shown
- First click "Run Agent Analysis" button in modal
- Or click "Get AI Suggestions" first, then view details

### Agents not running
- Check AGENTIC_ENABLED=true in backend/.env
- Verify LLM provider is configured
- Check backend logs for errors

## Summary

The **Agent Details** feature provides complete transparency into how LangGraph agents analyze flight disruptions. You can now:

✅ See every agent's input and output  
✅ Understand reasoning behind recommendations  
✅ Access raw data for debugging  
✅ View complete execution timeline  
✅ Re-run analysis on demand  
✅ Export/save audit trails  

**Click "View Full Agent Analysis" to see your AI agents in action!** 🚀
