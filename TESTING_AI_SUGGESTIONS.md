# Testing AI Suggestions in Agent Console

## What You Should See Now

1. **Navigate to Agent Console**: http://localhost:3000
2. **Look at the right sidebar** (Actions panel)
3. **You should see a NEW purple button**: "Get AI Suggestions" with a robot icon

## How to Test

### Step 1: Verify Backend is Ready

```bash
# Check agentic status
curl http://localhost:8000/api/agentic/status

# Should return:
{
  "enabled": true,  # ← Must be true
  "current_provider": "deepseek",
  "provider_configured": true  # ← Must be true
}
```

If `enabled: false`, update `backend/.env`:
```bash
AGENTIC_ENABLED=true
```

### Step 2: Use the AI Suggestions Button

1. **Open Agent Console**: http://localhost:3000
2. **Select a flight** from the dropdown (e.g., CX255)
3. **Select a passenger** from the list
4. **Click "Get AI Suggestions"** button in right panel
5. **Wait 5-15 seconds** (LangGraph workflow running)
6. **See AI recommendations appear** below the button

## What You'll See

### While Loading:
```
Button shows: "Running AI Analysis..."
(5-15 seconds depending on LLM provider)
```

### After Analysis:
A beautiful indigo card appears with:

**✨ AI Recommendations**
- **Strategy**: "Same-day alternative with premium protection"
- **Priority**: critical | Confidence: high
- **Est. Cost**: $45,000
- **Affected Pax**: 156

**For [Passenger Name]** (if passenger selected)
- Specific recommendation based on tier and needs

**📋 View AI Reasoning** (collapsible)
- Risk: Why this is high priority
- Rebooking: Strategy explanation
- Finance: Cost breakdown reasoning

## Test API Directly

```bash
# Test suggestions endpoint
curl http://localhost:8000/api/agent-reaccommodation/suggestions/CX255

# With specific passenger
curl "http://localhost:8000/api/agent-reaccommodation/suggestions/CX255?passenger_pnr=AA145J"

# Compare static vs AI
curl http://localhost:8000/api/agent-reaccommodation/compare/CX255
```

## Troubleshooting

### ❌ "Agentic analysis is not enabled"
**Fix**: Set `AGENTIC_ENABLED=true` in `backend/.env` and restart

### ❌ "LLM provider requires DEEPSEEK_API_KEY"
**Fix**: Your API key is already in .env (sk-d0bb73fd7be04c28a45a196f6c10b65e)
Verify with: `cat backend/.env | grep DEEPSEEK`

### ❌ Button not appearing
**Fix**: Hard refresh browser (Cmd+Shift+R) or restart frontend:
```bash
cd frontend/dashboard
npm run dev
```

### ❌ Error after clicking button
Check browser console (F12) and terminal logs for details.

Common issues:
- MongoDB not running → Start: `mongod --dbpath ./data/db`
- No flight data → Seed: `cd backend && uv run python ../scripts/generate_mock_data.py`
- API key invalid → Get new key from https://platform.deepseek.com/

## Expected Behavior

### First Click (Cold Start):
- LangGraph workflow executes all agents
- Takes 10-15 seconds
- Shows "Running AI Analysis..." 

### Subsequent Clicks:
- May use cached results (faster)
- Can force refresh with `force_refresh=true` parameter

## Cost Per Analysis

With DeepSeek (your current config):
- **$0.003-0.004 per analysis** ⭐ (very cheap!)
- ~15k tokens per flight
- 5-6 LLM calls (orchestrator + 4 sub-agents)

## What the AI Analyzes

The LangGraph workflow:
1. **Predictive Agent** → Detects if this is a real disruption
2. **Orchestrator Agent** → Creates main plan + what-if scenarios
3. **Risk Agent** → Assesses probability, duration, regulatory impact
4. **Rebooking Agent** → Determines strategy, hotel needs, VIP handling
5. **Finance Agent** → Estimates costs (compensation, hotels, ops)
6. **Crew Agent** → Identifies crew rotation needs
7. **Aggregator** → Combines all into final recommendation

All of this happens when you click the button!

## Compare with Static Options

The main panel shows **static MongoDB options** (pre-generated).
The AI button provides **dynamic analysis** with reasoning.

**Key Differences**:
| Feature | Static Options | AI Suggestions |
|---------|---------------|----------------|
| Source | MongoDB seed | LangGraph agents |
| Speed | Instant | 5-15 sec |
| Cost | Free | $0.004 |
| Reasoning | None | Full transparency |
| What-if | No | Yes |
| Context-aware | No | Yes (tier, PRM, etc.) |

## Success Indicators

✅ Button appears in right panel  
✅ Button is enabled (not grayed out)  
✅ Click shows "Running AI Analysis..."  
✅ After 5-15 sec, indigo card appears  
✅ Card shows strategy, priority, cost  
✅ "View AI Reasoning" is expandable  
✅ Terminal shows: `POST /api/agent-reaccommodation/suggestions/CX255`  

## Next Steps

Once working:
1. Try different flights to see varied recommendations
2. Compare AI vs static options
3. Click "View AI Reasoning" to see how agents think
4. Try with/without passenger selected (different recommendations)
5. Experiment with different LLM providers (OpenAI, Gemini, etc.)

---

**The AI suggestions are now live! Click the purple button to see LangGraph agents in action.** 🚀
