# Runway Ops Demo - Flight Disruption Management System

A production-ready flight disruption monitoring and management system featuring:
- **Real-time flight monitoring** with synthetic and live data providers
- **LangGraph multi-agent AI analysis** for disruption prediction and recommendations
- **Interactive dashboard** with crew, aircraft, and agentic insights
- **MongoDB persistence** for audit trails and historical analysis

## Architecture

### Backend (FastAPI + LangGraph)
- **Providers**: Synthetic, Realtime (aviationstack), MongoDB stream
- **Agentic System**: LangGraph orchestration with specialized AI agents
- **Persistence**: MongoDB for flight data, audit logs, simulations

### Frontend (React + Vite + Tailwind)
- Real-time flight monitor dashboard
- Crew and aircraft readiness panels
- AI analysis tab with what-if scenarios
- Responsive UI with shadcn/ui components

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- MongoDB (optional, for mongo mode and agentic persistence)
- OpenAI API key (for agentic system)

### 1. Install Dependencies

**Backend:**
```bash
cd backend
uv pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend/dashboard
npm install
```

### 2. Configure Environment

**Backend** (`backend/.env`):
```bash
# Flight monitor mode
FLIGHT_MONITOR_MODE=synthetic  # or: realtime, mongo

# For realtime mode
AVIATIONSTACK_API_KEY=your-key

# For agentic AI system (optional)
AGENTIC_ENABLED=true
OPENAI_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.2

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=runwayops
```

**Frontend** (`frontend/dashboard/.env.local`):
```bash
VITE_MONITOR_API=http://localhost:8000
VITE_DEFAULT_MONITOR_MODE=synthetic
```

### 3. Start Development Servers

Use the unified dev script:
```bash
./run_dev.sh
```

This starts:
- **Backend** (FastAPI): http://localhost:8000
- **Frontend** (Vite): http://localhost:3000
- **API Docs**: http://localhost:8000/docs

Or start individually:

**Backend only:**
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend only:**
```bash
cd frontend/dashboard
npm run dev
```

## Features

### 1. Flight Monitor
- Real-time departure tracking for HKG/CX
- Synthetic playbook scenarios or live aviationstack data
- Status categorization (normal, warning, critical)
- Flight details with turn progress, crew readiness, irregularities

### 2. Crew & Aircraft Panels
- Crew roster with fatigue risk and duty status
- Aircraft fleet status with maintenance tracking
- Readiness indicators and availability notes

### 3. **NEW: LangGraph Agentic Analysis**
- Multi-agent AI system for disruption analysis
- Specialized agents: Predictive, Risk, Rebooking, Finance, Crew
- What-if scenario simulation
- Transparent reasoning with full audit trails
- MongoDB-persisted analysis history
- **Multi-LLM Provider Support**: OpenAI, OpenRouter, DeepSeek, Gemini
- Flexible cost/quality trade-offs ($0.003 to $0.15 per analysis)

## Agentic System Usage

### Enable in Backend
```bash
# backend/.env
AGENTIC_ENABLED=true

# Choose your LLM provider
LLM_PROVIDER=openai  # or: openrouter, deepseek, gemini
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-your-key

# See LLM_PROVIDERS.md for other provider configurations
```

### Access in Dashboard
1. Navigate to http://localhost:3000
2. Click **"Run AI Analysis"** button in top nav
3. View results in **"AI Analysis"** tab

### API Endpoints
- `POST /api/agentic/analyze` - Run analysis
- `GET /api/agentic/status` - Check configuration
- `GET /api/agentic/history` - Past analyses
- `GET /api/agentic/simulations` - What-if history

See [AGENTIC_INTEGRATION.md](./AGENTIC_INTEGRATION.md) for complete documentation.

## Project Structure

```
runwayops_demo/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── agents/            # LangGraph agentic workflow
│   │   ├── providers/         # Data providers (synthetic, realtime, mongo)
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic & persistence
│   │   ├── schemas/           # Pydantic models
│   │   └── config.py          # Settings
│   └── requirements.txt
├── frontend/dashboard/        # React dashboard
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom hooks (flight monitor, agentic)
│   │   └── views/             # Page components
│   └── package.json
├── scripts/                   # Data generation scripts
├── mock/                      # Mock data fixtures
├── run_dev.sh                 # Unified dev server launcher
├── AGENTS.md                  # Repository guidelines
└── AGENTIC_INTEGRATION.md     # Agentic system documentation
```

## Testing

### Backend
```bash
cd backend
pytest  # (test suite to be added)
```

### Frontend
```bash
cd frontend/dashboard
npm run test  # (test suite to be added)
```

### Manual Testing
1. **Synthetic mode** (no external APIs):
   ```bash
   FLIGHT_MONITOR_MODE=synthetic ./run_dev.sh
   ```

2. **Realtime mode** (requires aviationstack key):
   ```bash
   FLIGHT_MONITOR_MODE=realtime AVIATIONSTACK_API_KEY=xxx ./run_dev.sh
   ```

3. **Agentic analysis** (requires OpenAI key):
   - Enable in `.env`
   - Run analysis from dashboard
   - Check MongoDB for audit logs:
     ```bash
     mongosh
     use runwayops
     db.agent_audit_logs.find().pretty()
     ```

## Data Modes

| Mode | Description | Requirements |
|------|-------------|--------------|
| `synthetic` | Deterministic playbook scenario | None |
| `realtime` | Live aviationstack API data | AVIATIONSTACK_API_KEY |
| `mongo` | MongoDB-streamed flight instances | MongoDB running |

## API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoints:
- `GET /api/flight-monitor` - Flight monitor data
- `POST /api/agentic/analyze` - AI disruption analysis
- `GET /api/reaccommodation/options` - Rebooking options

## Development

### Code Style
- **Backend**: Python 3.12, type hints, 4-space indent
- **Frontend**: TypeScript, React hooks, Tailwind CSS

### Adding a Provider
1. Implement `FlightMonitorProvider` in `backend/app/providers/`
2. Register in `resolve_provider()` in `__init__.py`
3. Update `ALLOWED_MODES` in `config.py`

### Adding an Agent
See `backend/app/agents/README.md` for extending the LangGraph workflow.

## Deployment

### Production Checklist
- [ ] Set strong `OPENAI_API_KEY` and `AVIATIONSTACK_API_KEY`
- [ ] Configure MongoDB with authentication
- [ ] Build frontend: `cd frontend/dashboard && npm run build`
- [ ] Use production ASGI server (e.g., uvicorn with workers)
- [ ] Enable HTTPS and CORS restrictions
- [ ] Monitor LLM API costs and set rate limits
- [ ] Set up log aggregation for audit trails

### Docker (Future)
```bash
docker-compose up
```

## Contributing

1. Follow guidelines in [AGENTS.md](./AGENTS.md)
2. Use conventional commit messages
3. Add tests for new features
4. Update documentation

## License

[Add license here]

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)

---

**Built for**: Cathay Pacific Hackathon  
**Stack**: Python, FastAPI, LangGraph, React, TypeScript, MongoDB  
**Status**: MVP → Production-Ready
