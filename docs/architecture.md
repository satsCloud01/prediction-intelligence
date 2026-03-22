# PredictionIntelligence - Architecture Documentation

## C1: System Context

```
                         +---------------------------+
                         |   Analysts / Strategists   |
                         |       (Browser Users)      |
                         +------------+--------------+
                                      |
                                      | HTTPS
                                      v
                         +---------------------------+
                         |   PredictionIntelligence   |
                         |                            |
                         |  AI-powered knowledge      |
                         |  graph simulation and      |
                         |  prediction platform       |
                         +-----+---------------+-----+
                               |               |
                               | HTTPS         | SQLite
                               v               v
                    +----------------+   +------------+
                    | LLM Providers  |   | Local File |
                    | (7 providers:  |   | System     |
                    |  Anthropic,    |   | (DB file)  |
                    |  OpenAI, etc.) |   +------------+
                    +----------------+
```

**Users**: Analysts, strategists, and domain experts who build knowledge graphs from seed documents, configure agent personas, run multi-round simulations, and explore AI-generated prediction reports.

**PredictionIntelligence**: A full-stack web application providing a 5-stage pipeline: Knowledge Graph Build, Environment Setup, Multi-Round Simulation, Report Generation, and Interactive Exploration.

**LLM Providers**: External AI services accessed via the Universal LLM Dispatcher supporting 7 providers (Anthropic, OpenAI, Google, Mistral, Groq, Together, Ollama). Used for graph extraction, agent reasoning during simulation rounds, report synthesis, and interactive Q&A. API keys are provided by the user (BYOK) and never persisted server-side.

---

## C2: Container Diagram

```
+-------------------------------------------------------------------+
|                      PredictionIntelligence                        |
|                                                                     |
|  +---------------------+        +-----------------------------+     |
|  |  Frontend            |        |  Backend                    |     |
|  |  (React 18 + Vite)   |  /api  |  (FastAPI + Python 3.12)   |     |
|  |                       +------->                             |     |
|  |  - React Router       |        |  - 8 API routers           |     |
|  |  - Tailwind CSS       |        |  - SQLAlchemy 2.0 async    |     |
|  |  - Recharts           |        |  - Pydantic v2 schemas     |     |
|  |  - React Flow         |        |  - Universal LLM Dispatcher|     |
|  |  - 11 pages + Landing |        |  - 5-stage pipeline engine |     |
|  |                       |        |                             |     |
|  |  Port 5183 (dev)     |        |  Port 8031 (uvicorn)       |     |
|  +---------------------+        +----------+--+---------------+     |
|                                             |  |                     |
|                                             |  |                     |
+---------------------------------------------|--|---------------------+
                                              |  |
                              HTTPS (optional) |  | File I/O
                                              v  v
                                  +-----------+  +-----------------+
                                  | LLM       |  | SQLite Database |
                                  | Providers  |  | predictor.db    |
                                  | (7 total)  |  +-----------------+
                                  +-----------+
```

### Frontend Container
- **Technology**: React 18, Vite, Tailwind CSS, Recharts, React Flow, React Router
- **Responsibilities**: Renders all UI pages, manages client-side state, stores LLM API keys in React state only (never persisted), proxies API calls to backend via Vite dev server
- **Pages** (11 + Landing): Dashboard, Projects, ProjectDetail, GraphBuilder, EnvironmentSetup, SimulationRunner, ReportView, Interaction, AgentGallery, Settings
- **Components**: Layout (sidebar navigation, collapsible, mobile-responsive), React Flow graph canvas, simulation timeline

### Backend Container
- **Technology**: FastAPI, Python 3.12, SQLAlchemy 2.0 (async), aiosqlite, Pydantic v2
- **Responsibilities**: REST API serving, database operations, LLM dispatch orchestration, 5-stage pipeline execution, file upload handling
- **Startup lifecycle**: `init_db()` (creates tables) then optional seed (populates if empty)
- **CORS**: Allows all origins (`*`)

### Database
- **Technology**: SQLite via aiosqlite (async driver)
- **File**: `backend/predictor.db` (auto-created on first run)
- **Tables**: 14 tables corresponding to 14 SQLAlchemy models

### LLM Providers
- **Universal LLM Dispatcher**: Supports Anthropic, OpenAI, Google, Mistral, Groq, Together, Ollama
- **Auth**: API key passed via `X-Api-Key` HTTP header from frontend; never stored server-side
- **Usage**: Graph extraction from seed documents, agent reasoning per simulation round, report synthesis, interactive chat

---

## C3: Component Diagram

### Backend Components

```
+------------------------------------------------------------------+
|                        FastAPI Application                         |
|                        (predictor.main)                           |
|                                                                    |
|  +------------------------------------------------------------+  |
|  |                     API Routers (8)                          |  |
|  |                                                              |  |
|  |  dashboard    projects    graph       agents                |  |
|  |  simulation   reports     interaction settings              |  |
|  +------+-----+-----------+------+-----+-----------+-----------+  |
|         |     |           |      |     |           |              |
|         v     v           v      v     v           v              |
|  +-------------+  +-------------+  +---------------------------+  |
|  | LLM         |  | Database    |  | SQLAlchemy Models (14)    |  |
|  | Dispatcher  |  | Module      |  |                           |  |
|  |             |  |             |  | Project, SeedDocument,    |  |
|  | 7 providers |  | engine      |  | KnowledgeNode,            |  |
|  | dispatch()  |  | async_session| | KnowledgeEdge,            |  |
|  | route_llm() |  | get_db()    |  | AgentPersona,             |  |
|  |             |  | init_db()   |  | SimulationRun,            |  |
|  +------+------+  +-------------+  | SimulationEvent,          |  |
|         |                           | AgentMessage,             |  |
|         v                           | PredictionReport,         |  |
|  +-------------+                    | InteractionSession,       |  |
|  | Provider    |                    | ChatMessage, AuditLog,    |  |
|  | SDKs        |                    | LLMUsageLog               |  |
|  | (anthropic, |                    +---------------------------+  |
|  |  openai,    |                                                   |
|  |  google,    |                    +---------------------------+  |
|  |  etc.)      |                    | Pipeline Engine           |  |
|  +-------------+                    | (5-stage orchestration)   |  |
|                                     | Graph Build -> Env Setup  |  |
|                                     | -> Simulation -> Report   |  |
|                                     | -> Interaction            |  |
|                                     +---------------------------+  |
+--------------------------------------------------------------------+
```

#### Router Responsibilities

| Router | Prefix | Purpose |
|--------|--------|---------|
| dashboard | `/api/dashboard` | Summary stats, pipeline status, recent activity |
| projects | `/api/projects` | CRUD for prediction projects, seed document upload |
| graph | `/api/graph` | CRUD for knowledge nodes and edges, graph extraction from documents |
| agents | `/api/agents` | CRUD for agent personas, persona gallery |
| simulation | `/api/simulation` | Create/run simulations, round-by-round execution, event log |
| reports | `/api/reports` | Generate/retrieve prediction reports, export (JSON) |
| interaction | `/api/interaction` | Interactive Q&A sessions against completed simulations |
| settings | `/api/settings` | App settings, LLM provider config, API key status |

#### Universal LLM Dispatcher

| Provider | SDK / Method | Models |
|----------|-------------|--------|
| Anthropic | `anthropic.Anthropic` | Claude family |
| OpenAI | `openai.OpenAI` | GPT-4, GPT-3.5, etc. |
| Google | `google.generativeai` | Gemini family |
| Mistral | `mistralai.Mistral` | Mistral family |
| Groq | `groq.Groq` | LLaMA, Mixtral on Groq |
| Together | `together.Together` | Open-source models |
| Ollama | HTTP to localhost | Local models |

### Frontend Components

```
+-------------------------------------------------------------------+
|                        React Application                           |
|                        (App.jsx)                                   |
|                                                                    |
|  +-------------------+  +--------------------------------------+  |
|  | Landing Page      |  | Layout (authenticated pages)         |  |
|  | (standalone)      |  |                                      |  |
|  +-------------------+  |  +--------+  +-------------------+  |  |
|                          |  |Sidebar |  | Page Content      |  |  |
|                          |  |Nav     |  | (10 pages)        |  |  |
|                          |  |        |  |                   |  |  |
|                          |  |API key |  | Dashboard         |  |  |
|                          |  |status  |  | Projects          |  |  |
|                          |  |indicator| | ProjectDetail     |  |  |
|                          |  |        |  | GraphBuilder      |  |  |
|                          |  |LLM     |  | EnvironmentSetup  |  |  |
|                          |  |provider|  | SimulationRunner  |  |  |
|                          |  |selector|  | ReportView        |  |  |
|                          |  |        |  | Interaction       |  |  |
|                          |  |Collapse|  | AgentGallery      |  |  |
|                          |  |toggle  |  | Settings          |  |  |
|                          |  +--------+  +-------------------+  |  |
|                          +--------------------------------------+  |
+-------------------------------------------------------------------+
```

#### API Client
- `request(path, options)` - Base fetch wrapper with JSON handling and error extraction
- `aiRequest(path, options)` - Extends `request()` by injecting `X-Api-Key` header from React state
- Named API methods organized by domain (projects, graph, agents, simulation, reports, interaction, settings)

---

## C4: Code-Level Detail

### llm_dispatcher.py

```
Module: predictor.llm_dispatcher

Universal LLM Dispatcher - routes requests to any of 7 supported providers.

Functions:
  dispatch(provider: str, api_key: str, model: str,
           system: str, prompt: str, max_tokens: int = 2000) -> str
      Routes to the appropriate provider client.
      Returns raw text content from LLM response.

  _call_anthropic(api_key, model, system, prompt, max_tokens) -> str
  _call_openai(api_key, model, system, prompt, max_tokens) -> str
  _call_google(api_key, model, system, prompt, max_tokens) -> str
  _call_mistral(api_key, model, system, prompt, max_tokens) -> str
  _call_groq(api_key, model, system, prompt, max_tokens) -> str
  _call_together(api_key, model, system, prompt, max_tokens) -> str
  _call_ollama(model, system, prompt, max_tokens) -> str

Each provider function:
  1. Instantiates provider SDK client with api_key
  2. Sends system + user prompt
  3. Returns text response
  4. Logs usage to LLMUsageLog
```

### pipeline.py

```
Module: predictor.pipeline

5-Stage Pipeline Orchestration:

Stage 1 - Graph Build:
  build_knowledge_graph(project_id, api_key, provider, model) -> dict
      Reads seed documents for the project.
      Sends document text to LLM with extraction prompt.
      Parses response into KnowledgeNode and KnowledgeEdge records.
      Returns node/edge counts.

Stage 2 - Environment Setup:
  setup_environment(project_id, agent_configs) -> dict
      Creates/updates AgentPersona records for the project.
      Validates agent configurations against graph nodes.
      Returns environment summary.

Stage 3 - Simulation:
  run_simulation(project_id, api_key, provider, model, rounds) -> dict
      Creates SimulationRun record.
      For each round:
        - Each agent receives graph context + prior messages
        - LLM generates agent response (reasoning, predictions, interactions)
        - Creates SimulationEvent and AgentMessage records
      Returns simulation_id, total_events, total_messages.

Stage 4 - Report:
  generate_report(simulation_id, api_key, provider, model) -> dict
      Reads all simulation events and agent messages.
      Sends to LLM for synthesis into prediction report.
      Creates PredictionReport record.
      Returns report_id, summary.

Stage 5 - Interaction:
  start_interaction(report_id) -> dict
      Creates InteractionSession linked to report.
      Returns session_id.

  chat(session_id, user_message, api_key, provider, model) -> dict
      Loads report context + chat history.
      Sends to LLM for contextual response.
      Creates ChatMessage records (user + assistant).
      Returns assistant response.
```

### models.py

```
Module: predictor.models
Base: SQLAlchemy DeclarativeBase (from predictor.database)

All models use Integer primary key, DateTime created_at (UTC default).
JSON columns store lists/dicts as native JSON (SQLite JSON1).

14 Models:
  Project            - name, description, status, config (JSON)
  SeedDocument       - project_id (FK), filename, content, doc_type, uploaded_at
  KnowledgeNode      - project_id (FK), label, node_type, properties (JSON),
                       position_x, position_y
  KnowledgeEdge      - project_id (FK), source_node_id (FK), target_node_id (FK),
                       relationship, weight, properties (JSON)
  AgentPersona       - project_id (FK), name, role, personality, expertise (JSON),
                       goals (JSON), constraints (JSON)
  SimulationRun      - project_id (FK), status, rounds_total, rounds_completed,
                       config (JSON), started_at, completed_at
  SimulationEvent    - simulation_id (FK), round_number, agent_id (FK),
                       event_type, content (JSON), timestamp
  AgentMessage       - simulation_id (FK), round_number, sender_agent_id (FK),
                       receiver_agent_id (FK, nullable), message_type,
                       content, reasoning
  PredictionReport   - simulation_id (FK), title, summary, predictions (JSON),
                       confidence_scores (JSON), methodology, generated_at
  InteractionSession - report_id (FK), status, started_at, ended_at
  ChatMessage        - session_id (FK), role, content, timestamp
  AuditLog           - entity_type, entity_id, action, details (JSON), timestamp
  LLMUsageLog        - provider, model, prompt_tokens, completion_tokens,
                       total_tokens, latency_ms, endpoint, timestamp
```

### database.py

```
Module: predictor.database

DATABASE_URL: "sqlite+aiosqlite:///<path>/predictor.db"
engine: AsyncEngine (echo=False)
async_session: async_sessionmaker[AsyncSession]
Base: DeclarativeBase

Functions:
  get_db() -> AsyncGenerator[AsyncSession]   (FastAPI dependency)
  init_db() -> None                          (creates all tables)
```
