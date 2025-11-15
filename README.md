# Runway Ops Demo - Flight Disruption Management System

A production-ready Integrated Operations Centre (IOC) system for airline flight disruption management, combining real-time monitoring with AI-powered decision support:

- **Real-time Flight Monitoring** - Live dashboard tracking HKG/CX operations with synthetic, live (aviationstack), or MongoDB data modes
- **AI-Powered Disruption Analysis** - Google ADK multi-agent system for predictive alerts, re-accommodation, cost analysis, and crew planning
- **IOC Dashboard** - Passenger cohort management with disruption queues and re-accommodation workflows
- **What-If Scenario Simulator** - Test disruption scenarios and view AI-generated outcomes before taking action
- **Predictive Signals** - ML-driven risk assessment with weather, crew, and aircraft signal analysis
- **Multi-Provider LLM Support** - OpenAI, OpenRouter, DeepSeek, Gemini with flexible cost/quality trade-offs
- **Amadeus Integration** - Optional live flight and hotel search for real re-accommodation data
- **MongoDB Persistence** - Audit trails, agent decisions, simulation history, and mock data infrastructure

## Tech Stack

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agents-000000)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)
![Tailwind_CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?logo=tailwindcss&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7-47A248?logo=mongodb&logoColor=white)

Backend runs on Python/FastAPI + LangGraph, frontend on React/TypeScript + Vite/Tailwind, with MongoDB used for
agentic audit history, mock flight data, and the optional `mongo` data mode.

## Architecture

### Backend (FastAPI + Google ADK)

**API Layer (FastAPI 0.115)**
- RESTful + Server-Sent Events (SSE) for real-time what-if analysis
- CORS-enabled for local/production deployment
- OpenAPI/Swagger documentation at `/docs`

**Data Providers** (`app/providers/`)
- `synthetic.py` - Deterministic playbook scenarios with 7 pre-defined flights
- `realtime.py` - Live aviationstack API integration with fallback logic
- `mongo_stream.py` - MongoDB-backed real-time data streaming
- `shared.py` - Common utilities for crew/aircraft/passenger generation

**Agentic System** (`app/agentsv2/` - Google ADK-compatible)
- **PredictiveAgent** - Disruption detection from weather/crew/aircraft signals
- **OrchestratorAgent** - Plans actions and generates what-if scenarios
- **RiskAgent** - Assesses likelihood, duration, regulatory impact
- **RebookingAgent** - Passenger re-accommodation with Amadeus or synthetic data
- **FinanceAgent** - EU261/HKCAD compliance cost calculations
- **CrewAgent** - Duty time monitoring and backup crew planning
- **AggregatorAgent** - Synthesizes outputs into final action plan
- **Workflow** - Sequential + parallel execution with audit logging

**Services** (`app/services/`)
- `predictive_signals.py` - ML-based risk probability computation
- `disruption_updater.py` - Automatic signal updates every 30s
- `agentic.py` - Multi-LLM orchestration (OpenAI/DeepSeek/Gemini/OpenRouter)
- `amadeus_client.py` - Flight offers, hotels, pricing, booking
- `mongo_client.py` - MongoDB connection pooling
- `reaccommodation.py` - Static MongoDB-based options

**Persistence (MongoDB)**
- `flight_manifests` - Flight + passenger cohorts
- `passengers` - Cathay Profile, loyalty tier, special assistance
- `crew` - Duty hours, fatigue risk, readiness state
- `aircraft` - Maintenance history, status, availability
- `disruptions` - Root cause, impact, cost estimates
- `agent_audit_logs` - Full agent execution traces
- `agent_simulations` - What-if scenario history

### Frontend (React 18 + TypeScript + Vite)

**Views** (`src/views/`)
- `RealtimeFlightMonitor.tsx` - Main ops dashboard (flights, crew, aircraft, agentic analysis tabs)
- `IOCQueues.tsx` - Disruption cohort management with AI-powered finance/rebooking cards
- `CohortDetail.tsx` - Per-flight passenger list with tier breakdown and options
- `WhatIfScenario.tsx` - Interactive scenario simulator with real-time agent progress
- `AgentPassengerPanel.tsx` - Passenger-specific AI recommendations
- `Reports.tsx` - Analytics and trend visualization
- `AgenticDebugPanel.tsx` - Developer agent inspection tool

**State Management**
- `AgenticContext` - Global agentic engine selection, monitor config
- Custom hooks for flight data, agent analysis, re-accommodation

**UI Components** (shadcn/ui + Tailwind)
- Radix UI primitives (Dialog, Dropdown, Select, Tabs, etc.)
- Lucide React icons
- Recharts for trend visualization
- Sonner for toast notifications

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB Community Server 7.0+ (required for `mongo` mode, mock data scripts, and agentic persistence)
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

### 4. MongoDB Setup (Optional)

MongoDB is required for:
- **`mongo` data mode** - Real-time streaming from MongoDB collections
- **Agentic audit logs** - Agent execution history and decision traces
- **Mock data scripts** - Populating realistic demo data
- **What-if simulation history** - Storing scenario analysis results

**Installation:**
```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community

# Ubuntu/Debian
sudo apt-get install -y mongodb-org
sudo systemctl start mongod

# Verify installation
mongosh --eval 'db.version()'
```

**Populate Mock Data:**
```bash
# Generate flight manifests, passengers, crew, aircraft, disruptions
python scripts/generate_mock_data.py

# Start real-time ticker (updates flight delays, crew readiness)
python scripts/flight_ticker.py --iterations 0 --sleep 30
```

Default connection: `mongodb://localhost:27017` (database: `runwayops`)

## Key Features

### 1. Real-Time Flight Monitor
**Tracks live operations for HKG/CX with 30-second refresh**
- 📊 Summary metrics: total flights, avg delay, impacted passengers, turn reliability, crew readiness
- ✈️ Flight cards with status (normal/warning/critical), delay, pax impact, connections
- 🎯 Turn progress tracking: crew inbound, clean, fuel, boarding, pushback
- ⚠️ Predictive alerts with risk drivers and AI recommendations
- 📈 Trend charts: movements/hour, average delay over time
- 🔄 Auto-refresh with manual override
- 📡 Data modes: synthetic (playbook), realtime (aviationstack), mongo (streaming)

### 2. IOC Dashboard (Disruption Cohort Management)
**Central hub for operations controllers managing disruptions**
- 👥 Passenger cohorts grouped by disrupted flight
- 📋 Tier breakdown (Diamond, Gold, Silver, Green) per cohort
- 💰 AI-powered finance impact cards (compensation, hotels, operational costs)
- ✈️ AI-powered re-accommodation cards (strategies, flight options, hotel arrangements)
- 🎯 Suitability scoring for rebooking options
- ⚠️ Exception flagging for manual review (PRM, infants, VIPs)
- 🔗 Deep-link to passenger detail views
- 🌍 Amadeus integration indicator (live data when configured)

### 3. What-If Scenario Simulator
**Safe sandbox for testing disruption scenarios before production**
- 🎛️ Configurable parameters:
  - Additional delay (0-180 minutes)
  - Weather impact (none/minor/moderate/severe)
  - Crew unavailability (count)
  - Aircraft maintenance issues
  - Connection pressure (low/medium/high)
  - Passenger count changes
- 🤖 Real-time AI analysis with agent progress timeline
- 📊 Predicted outcomes:
  - Disruption likelihood
  - Risk level comparison (baseline → predicted)
  - Financial impact estimate
  - Passengers affected
  - Recommended actions
- 🔍 Per-agent decision breakdown (Risk, Rebooking, Finance, Crew)
- 💾 Scenario summary before execution
- 📡 Server-Sent Events (SSE) for live progress updates

### 4. Google ADK Multi-Agent System
**Hierarchical AI workflow for disruption analysis**
- 🧠 **PredictiveAgent**: Weather/crew/aircraft signal analysis → disruption detection
- 🎯 **OrchestratorAgent**: Creates action plans and simulates what-if scenarios
- 🛡️ **RiskAgent**: Probability, duration, regulatory impact, passenger safety
- ✈️ **RebookingAgent**: Re-accommodation with Amadeus or synthetic flight/hotel options
- 💰 **FinanceAgent**: EU261/HKCAD compensation + operational costs
- 👥 **CrewAgent**: Duty time limits, backup crew, regulatory compliance
- 📊 **AggregatorAgent**: Synthesizes outputs into final action plan with confidence score
- 📋 Full audit logging with timestamps and reasoning chains
- 🔄 MongoDB persistence for history and compliance

### 5. Multi-LLM Provider Support
**Flexible model selection based on cost/quality trade-offs**
- **OpenAI** (GPT-4o, GPT-4 Turbo) - Best quality, $$$ cost
- **OpenRouter** (Claude 3.5, Gemini, Llama 3.1) - Multi-provider access, $$ cost
- **DeepSeek** (DeepSeek Chat, Coder) - Cost-effective, $ cost
- **Google Gemini** (Pro, 1.5 Pro, Flash) - Fast responses, $ cost
- Configurable temperature and model per provider
- Automatic fallback to heuristics if LLM unavailable
- Per-analysis cost: $0.003 to $0.15 depending on provider/model

### 6. Predictive Signals & Risk Assessment
**ML-driven disruption prediction integrated into flight data**
- 🌤️ Weather signal analysis (keywords, severity)
- 👥 Crew fatigue and readiness scoring
- ✈️ Aircraft maintenance status evaluation
- 📊 Weighted risk probability calculation
- 💡 Flight-specific recommendations
- ⏱️ Auto-updates every 30 seconds with disruption ticker
- 🎯 Risk drivers with evidence (shown in alert modals)
- 📈 Severity levels: LOW / MEDIUM / HIGH

### 7. Amadeus Integration (Optional)
**Live flight and hotel data for real re-accommodation**
- ✈️ Flight offer search (origin/destination/date/passenger count)
- 🏨 Hotel search (city/check-in/check-out/rooms)
- 💰 Pricing confirmation and booking creation
- 📡 OAuth2 token management with auto-refresh
- 🧪 Test environment support for development
- 🔄 Automatic fallback to synthetic if credentials missing
- Data source indicator: "Amadeus (live)" vs "Synthetic (playbook)"

### 8. Crew & Aircraft Management
**Real-time operational readiness tracking**
- 👥 **Crew Panel**:
  - Assignment status (on duty, standby, rest)
  - Fatigue risk indicators (low/medium/high)
  - Duty time remaining (FDP hours)
  - Current duty phase (report, briefing, boarding, etc.)
  - Readiness state (ready, standby, hold)
  - Communication preferences
- ✈️ **Aircraft Panel**:
  - Fleet status (active, maintenance, AOG, storage)
  - Maintenance history (A-check, C-check dates)
  - Engine hours and cycles
  - APU status
  - Compatibility with airports/gates
  - Status notes with context

### 9. Passenger Detail & Profiling
**Cathay-specific passenger management**
- 🎫 PNR and booking reference tracking
- 🏆 Loyalty tier (Diamond, Gold, Silver, Green) with benefits
- ♿ Special assistance flags (wheelchair, meal preferences)
- 👶 Family travel indicators (infants, groups)
- 💳 Revenue value and booking class
- 📱 Contact preferences (app, email, SMS)
- ✈️ Original flight details and disruption context

### 10. Developer Tools
**Built-in debugging and configuration**
- 🧪 Agent execution inspector with audit logs
- 🎛️ Runtime agentic engine switcher (apiv2)
- 📡 Data source selector (synthetic/realtime/mongo)
- 🌍 Airport and carrier override
- 📊 UI state testing (empty, loading, error states)
- 📋 OpenAPI documentation at `/docs`
- 🔍 Detailed logging with agent communication traces

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
2. Select view: **Realtime Monitor** / **IOC Dashboard** / **What-If Analysis**
3. Click **"Run AI Analysis"** or enable in Dev Tools menu
4. View results in dedicated tabs or cards

### API Endpoints
**Core Flight Monitor:**
- `GET /api/flight-monitor` - Real-time flight data with predictive signals
- `GET /api/predictive-alerts/{flight_number}` - Flight-specific risk analysis

**Agentic Analysis:**
- `POST /api/agentic/analyze` - Run full multi-agent analysis
- `GET /api/agentic/status` - Check configuration and available engines
- `GET /api/agentic/history` - Past analysis results
- `GET /api/agentic/simulations` - What-if scenario history
- `GET /api/agentic/providers` - LLM provider details

**What-If Scenarios:**
- `GET /api/whatif/analyze-stream` - Real-time SSE analysis with agent progress
- `POST /api/whatif/analyze` - Synchronous scenario analysis
- `GET /api/whatif/predict/{flight_number}` - Quick prediction without full workflow

**Agent-Powered Re-accommodation:**
- `GET /api/agent-options/flights/{flight_number}` - AI-generated rebooking options
- `GET /api/agent-options/passengers/{pnr}/options` - Passenger-specific recommendations
- `POST /api/agent-reaccommodation/analyze/{flight_number}` - Full agent analysis
- `GET /api/agent-reaccommodation/suggestions/{flight_number}` - Quick suggestions
- `GET /api/agent-reaccommodation/compare/{flight_number}` - Static vs AI comparison

**Static Re-accommodation (MongoDB):**
- `GET /api/reaccommodation/flights` - List disrupted flights
- `GET /api/reaccommodation/flights/{flight_number}/manifest` - Flight manifest
- `GET /api/reaccommodation/passengers/{pnr}` - Passenger details

Full API documentation: http://localhost:8000/docs

## Project Structure

```
runwayops_demo/
├── backend/                              # FastAPI application
│   ├── app/
│   │   ├── agentsv2/                    # Google ADK agentic workflow (APIV2)
│   │   │   ├── agents.py                # Agent implementations
│   │   │   ├── workflow.py              # Orchestration logic
│   │   │   ├── tools.py                 # Custom tools (predictive, rebooking, etc.)
│   │   │   ├── state.py                 # Pydantic state model
│   │   │   ├── api.py                   # APIV2 router
│   │   │   └── tests/                   # Agent test suite
│   │   ├── providers/                   # Data providers
│   │   │   ├── synthetic.py             # Playbook scenarios
│   │   │   ├── realtime.py              # Aviationstack integration
│   │   │   ├── mongo_stream.py          # MongoDB streaming
│   │   │   └── shared.py                # Common utilities
│   │   ├── routes/                      # API endpoints
│   │   │   ├── whatif.py                # What-if scenario analysis
│   │   │   ├── agentic.py               # General agentic endpoints
│   │   │   ├── agent_options.py         # AI-powered rebooking
│   │   │   ├── agent_reaccommodation.py # Agent analysis endpoints
│   │   │   └── reaccommodation.py       # Static MongoDB options
│   │   ├── services/                    # Business logic & integrations
│   │   │   ├── agentic.py               # Multi-LLM orchestration
│   │   │   ├── amadeus_client.py        # Amadeus API client
│   │   │   ├── predictive_signals.py    # Risk computation
│   │   │   ├── disruption_updater.py    # Auto-signal updates
│   │   │   ├── mongo_client.py          # MongoDB connection
│   │   │   └── reaccommodation.py       # Static option logic
│   │   ├── schemas/                     # Pydantic models
│   │   ├── config.py                    # Settings & env vars
│   │   ├── main.py                      # FastAPI app & routes
│   │   └── exceptions.py                # Custom exceptions
│   ├── requirements.txt                 # Python dependencies
│   └── .env.example                     # Environment template
├── frontend/dashboard/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── views/                       # Main application views
│   │   │   ├── RealtimeFlightMonitor.tsx
│   │   │   ├── IOCQueues.tsx
│   │   │   ├── WhatIfScenario.tsx
│   │   │   ├── CohortDetail.tsx
│   │   │   ├── AgentPassengerPanel.tsx
│   │   │   ├── Reports.tsx
│   │   │   └── AgenticDebugPanel.tsx
│   │   ├── components/                  # Reusable UI components
│   │   │   └── ui/                      # shadcn/ui primitives
│   │   ├── hooks/                       # Custom React hooks
│   │   │   ├── useFlightMonitor.ts
│   │   │   ├── useAgenticAnalysis.ts
│   │   │   ├── useAgentOptions.ts
│   │   │   ├── useAgentReaccommodation.ts
│   │   │   ├── usePredictiveAlerts.ts
│   │   │   └── useReaccommodation.ts
│   │   ├── context/                     # React context providers
│   │   │   └── AgenticContext.tsx
│   │   ├── types/                       # TypeScript type definitions
│   │   ├── lib/                         # Utilities & helpers
│   │   ├── App.tsx                      # Main app shell
│   │   └── main.tsx                     # Entry point
│   ├── package.json                     # Frontend dependencies
│   └── .env.example                     # Environment template
├── scripts/                              # Data generation & utilities
│   ├── generate_mock_data.py            # Populate MongoDB fixtures
│   ├── flight_ticker.py                 # Real-time delay simulator
│   └── debug_agents.py                  # Agent testing tool
├── mock/                                 # JSON fixtures
│   ├── disruptions.json
│   ├── crew.json
│   ├── passengers.json
│   └── aircraft.json
├── data/                                 # MongoDB data directory (gitignored)
├── run_dev.sh                            # Unified dev server launcher
├── run_prod.sh                           # Production server script
├── install.sh                            # Dependency installer
├── AGENTS.md                             # Repository guidelines
├── LLM_PROVIDERS.md                      # LLM configuration guide
├── PREDICTIVE_SIGNALS_INTEGRATION.md     # Predictive signals docs
├── AMADEUS_INTEGRATION_GUIDE.md          # Amadeus setup guide
└── README.md                             # This file
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

| Mode          | Description                       | Requirements          |
| ------------- | --------------------------------- | --------------------- |
| `synthetic` | Deterministic playbook scenario   | None                  |
| `realtime`  | Live aviationstack API data       | AVIATIONSTACK_API_KEY |
| `mongo`     | MongoDB-streamed flight instances | MongoDB running       |

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

See `backend/app/agentsv2/README.md` for extending the Google ADK workflow:
1. Define tools in `tools.py` as async functions
2. Create agent classes in `agents.py` extending `BaseAgent`
3. Update workflow orchestration in `workflow.py`
4. Add tests in `tests/`
5. Document in agent README

### Environment Variables Reference

**Backend (`backend/.env`):**
```bash
# Flight monitor
FLIGHT_MONITOR_MODE=synthetic              # or: realtime, mongo
AVIATIONSTACK_API_KEY=your-key            # for realtime mode

# Agentic system
AGENTIC_ENABLED=true
AGENTIC_MODE=apiv2                        # Only APIV2 (ADK) supported

# LLM provider
LLM_PROVIDER=openai                       # openai, openrouter, deepseek, gemini
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.2
OPENAI_API_KEY=sk-your-key
# See LLM_PROVIDERS.md for other providers

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=runwayops

# Amadeus (optional)
AMADEUS_CLIENT_ID=your-client-id
AMADEUS_CLIENT_SECRET=your-secret
AMADEUS_ENVIRONMENT=test                  # test or production
```

**Frontend (`frontend/dashboard/.env.local`):**
```bash
VITE_MONITOR_API=http://localhost:8000
VITE_DEFAULT_MONITOR_MODE=synthetic
```

## Deployment

### Production Checklist

- [ ] **API Keys**: Set strong `OPENAI_API_KEY`, `AVIATIONSTACK_API_KEY`, optional `AMADEUS_CLIENT_ID/SECRET`
- [ ] **MongoDB**: Configure with authentication, enable SSL/TLS
  ```bash
  MONGO_URI=mongodb://user:pass@host:27017/runwayops?authSource=admin&ssl=true
  ```
- [ ] **Frontend Build**: 
  ```bash
  cd frontend/dashboard
  npm run build
  # Serve from frontend/dashboard/dist/
  ```
- [ ] **Backend Server**: Use production ASGI server
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- [ ] **CORS**: Update `CORSMiddleware` allow_origins to specific domains
- [ ] **HTTPS**: Enable SSL/TLS termination (nginx/load balancer)
- [ ] **Monitoring**:
  - LLM API costs and rate limits
  - MongoDB query performance
  - Agent execution times
  - Predictive signal accuracy
- [ ] **Logging**: Set up centralized log aggregation for audit trails
- [ ] **Secrets**: Use environment-specific secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] **Backup**: Schedule MongoDB backups (`agent_audit_logs`, `agent_simulations`)

### Docker & Local Containers

```bash
# Build and run backend + frontend + Mongo
docker compose up --build

# Environment
# - backend/.env required (copied from backend/.env.example)
# - VITE_MONITOR_API defaults to http://localhost:8000 (configurable via build arg)
```

Services:
- **mongo**: MongoDB 7.0 (port 27017)
- **backend**: FastAPI (port 8000)
- **frontend**: Nginx serving built Vite app (port 3000)

### Google Cloud Run

Prerequisites:
- gcloud CLI, Docker
- Artifact Registry enabled
- `backend/.env.deploy` with production env vars

Deploy:
```bash
# From repo root
cp backend/.env.deploy.example backend/.env.deploy
# Fill in API keys and Mongo URI

# Deploy (requires PROJECT_ID configured via gcloud or env var)
./deploy.sh

# Optional overrides
PROJECT_ID=my-project REGION=asia-southeast1 ./deploy.sh
```

Script actions:
1. Builds backend & frontend Docker images
2. Pushes to Artifact Registry `$REGION-docker.pkg.dev/$PROJECT_ID/runwayops`
3. Deploys backend to Cloud Run (defaults: service `runwayops-backend`, port 8000)
4. Deploys frontend to Cloud Run (service `runwayops-frontend`, port 80)
5. Sets frontend `VITE_MONITOR_API` to backend URL unless overridden

Post-deploy:
- Configure MongoDB Atlas / Cloud Mongo instance and update `MONGO_URI`
- Add custom domains & HTTPS via Cloud Run
- Set IAM policies for private/public access as needed

### Production Scripts

```bash
# Check if backend is running
./run_prod.sh --check

# Start in production mode
./run_prod.sh
```

### Docker (Planned)

```bash
# Build and start all services
docker-compose up --build

# Services:
# - backend (FastAPI)
# - frontend (nginx serving static build)
# - mongodb
# - redis (for caching, if needed)
```

## Contributing

1. **Follow Guidelines**: See [AGENTS.md](./AGENTS.md) for coding standards
   - Python 3.12, type hints, 4-space indent
   - TypeScript with React hooks
   - Exhaustive logging for agent operations
2. **Commit Messages**: Use conventional commits
   ```
   feat: add Amadeus hotel search integration
   fix: correct risk probability calculation
   docs: update API endpoint documentation
   ```
3. **Testing**: Add tests for new features
   - Backend: `pytest backend/app/agentsv2/tests/`
   - Frontend: `npm run test` (to be implemented)
4. **Documentation**: Update relevant docs
   - README.md for major features
   - Inline docstrings for functions/classes
   - API examples in `/docs`
5. **Pull Requests**: 
   - Describe behavior changes
   - Link to design docs or issues
   - Include manual verification steps
   - Call out any new dependencies

## Documentation

- **[AGENTS.md](./AGENTS.md)** - Repository guidelines and architecture notes
- **[LLM_PROVIDERS.md](./LLM_PROVIDERS.md)** - Complete LLM configuration guide with cost comparisons
- **[PREDICTIVE_SIGNALS_INTEGRATION.md](./PREDICTIVE_SIGNALS_INTEGRATION.md)** - Predictive signals system docs
- **[AMADEUS_INTEGRATION_GUIDE.md](./AMADEUS_INTEGRATION_GUIDE.md)** - Amadeus API setup and usage
- **[backend/app/agentsv2/README.md](./backend/app/agentsv2/README.md)** - Google ADK agent implementation details
- **[APIV2_MIGRATION_SUMMARY.md](./APIV2_MIGRATION_SUMMARY.md)** - Migration from LangGraph to ADK
- **[MULTI_PROVIDER_SUMMARY.md](./MULTI_PROVIDER_SUMMARY.md)** - Multi-LLM provider architecture

## Resources & References

**Frameworks & Libraries:**
- [Google ADK](https://google.github.io/adk-docs/) - Agent Development Kit
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Original agentic framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend API framework
- [React](https://react.dev/) - Frontend library
- [Vite](https://vitejs.dev/) - Build tool
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [shadcn/ui](https://ui.shadcn.com/) - UI component library
- [Recharts](https://recharts.org/) - Chart visualization

**APIs & Services:**
- [Amadeus Self-Service APIs](https://developers.amadeus.com/) - Flight & hotel data
- [AviationStack](https://aviationstack.com/) - Real-time flight tracking
- [MongoDB](https://www.mongodb.com/docs/) - Database
- [OpenAI](https://platform.openai.com/docs/) - GPT models
- [OpenRouter](https://openrouter.ai/) - Multi-model access
- [DeepSeek](https://platform.deepseek.com/) - Cost-effective LLM
- [Google Gemini](https://ai.google.dev/) - Gemini models

**Compliance & Standards:**
- [EU261 Regulation](https://europa.eu/youreurope/citizens/travel/passenger-rights/air/index_en.htm) - Air passenger rights
- [HKCAD](https://www.cad.gov.hk/) - Hong Kong Civil Aviation Department

---

**Built for**: Cathay Pacific Operations / Hackathon Demo  
**Primary Stack**: Python 3.12 • FastAPI • Google ADK • React 18 • TypeScript • MongoDB 7  
**Status**: Production-Ready MVP with Amadeus Integration  
**License**: [Specify License]
