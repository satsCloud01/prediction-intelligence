# PredictionIntelligence - Constraints

## Technology Stack Constraints

### Backend
- **Python 3.12** required
- **FastAPI** with async request handlers
- **SQLAlchemy 2.0** with async engine -- requires `aiosqlite` and `greenlet` packages
- **SQLite** as the sole database -- no external database server required
- **Universal LLM Dispatcher** supporting 7 providers (Anthropic, OpenAI, Google, Mistral, Groq, Together, Ollama)
- **Pydantic v2** for all request/response validation
- All database operations are async via `AsyncSession`

### Frontend
- **React 18** with functional components and hooks only (no class components)
- **Vite** as build tool and dev server
- **Tailwind CSS** for styling
- **React Router** for client-side routing
- **Recharts** for data visualization (charts, confidence scores)
- **React Flow** for knowledge graph visualization and editing
- No TypeScript -- plain JSX throughout
- No state management library (React state + prop drilling)

### Shared
- Frontend proxies `/api` requests to backend via Vite dev server config
- No authentication/authorization system (open access to all endpoints)
- No WebSocket or real-time features -- simulation progress is polled or returned synchronously

---

## Security Constraints

### API Key Management (BYOK)
- LLM API keys are stored **exclusively in React component state** -- never in localStorage, never persisted to disk
- Frontend sends the key via `X-Api-Key` HTTP header on LLM-dependent requests only
- Backend **never** stores API keys in the database -- the settings router explicitly rejects any key containing "api_key"
- Keys are visible in browser dev tools (memory and network headers) during the session
- Keys are lost when the browser tab is closed or refreshed (by design)

### CORS
- CORS is configured with `allow_origins=["*"]` -- any origin can make requests
- `allow_credentials=True` and all methods/headers are permitted
- This is a demo/pitch application configuration, not production-hardened

### Data Privacy
- Seed document content is sent to LLM providers during graph extraction and simulation
- No data encryption at rest (SQLite file is unencrypted)
- Audit log tracks actions but not data payloads
- LLM usage log records token counts but not prompt/response content

### No Authentication
- All API endpoints are publicly accessible (no login, no session management, no RBAC)
- The only "auth" is the optional X-Api-Key header for LLM features, which authenticates with the LLM provider, not with the application itself

---

## Performance Constraints

### Database
- SQLite is single-writer -- concurrent write operations are serialized
- No connection pooling configuration (default aiosqlite behavior)
- JSON columns (properties, config, predictions, expertise, goals, etc.) are not indexed -- queries filtering by JSON content require full table scans
- Cascade deletes on project removal can be expensive if the project has large graphs and many simulation rounds

### LLM Service
- Simulation execution is **synchronous per round** -- each agent's LLM call must complete before the next agent in the same round
- No request caching -- repeated identical LLM requests make fresh API calls
- No rate limiting on LLM endpoints (relies on provider-side rate limits)
- No streaming -- full response must complete before returning
- Multi-round simulation with N agents and R rounds requires N x R LLM calls minimum
- Large knowledge graphs may exceed context window limits for some models

### Frontend
- No pagination on list endpoints -- all records are returned in a single response
- No client-side caching or state persistence (API keys and all state lost on refresh)
- React Flow performance degrades with graphs exceeding ~500 nodes
- No lazy loading of page components
- No service worker or offline support

---

## Deployment Constraints

### Local Development
- Backend requires Python 3.12 virtual environment at `backend/.venv/`
- Run backend: `cd backend && PYTHONPATH=src .venv/bin/uvicorn predictor.main:app --reload --port 8031`
- Run frontend: `cd frontend && npm run dev` (port 5183, proxies /api to :8031)
- Node.js must be available
- No `.env` file required -- the only external dependency (LLM API keys) is provided via the browser UI

### Docker / Production
- Dockerfile builds both frontend (static) and backend (uvicorn) into a single container
- Production image pushed to AWS ECR
- Deployed on consolidated EC2 instance via Docker (port 8031 mapped)
- Frontend production build: `npm run build` (outputs to `dist/`, served by FastAPI static mount)
- Backend runs as single uvicorn process (no gunicorn workers for SQLite compatibility)
- Health check endpoint at `/api/health` for container orchestration

### Database
- SQLite database file is created at `backend/predictor.db`
- Database is auto-created on first application startup via `init_db()`
- No migration system -- schema changes require deleting the database file and restarting
- Database file is ephemeral in Docker (lost on container rebuild unless volume-mounted)

---

## Data Constraints

### SQLite Limitations
- Maximum database size: 281 TB (theoretical) -- practical limit depends on disk
- No concurrent writes -- all writes are serialized through SQLite's file-level lock
- JSON columns use SQLite JSON1 extension (available by default in Python's sqlite3)
- No full-text search capability on document content
- DateTime stored as ISO strings (SQLite has no native datetime type)

### LLM Response Parsing
- LLM responses are expected to be valid JSON for graph extraction and report generation
- Fallback parsing: tries full response first, then extracts content between first `{` and last `}`
- Malformed LLM responses result in partial or empty results (not retried automatically)

### File Upload
- Seed documents accepted as text, PDF, markdown, CSV
- Text extraction from PDFs depends on backend library availability
- No file size limit enforced at application level (limited by uvicorn request size defaults)
- Uploaded file content is stored in the database as text, not on the filesystem

---

## Operational Constraints

### Monitoring
- LLMUsageLog table tracks all LLM API calls (provider, model, tokens, latency)
- AuditLog table tracks entity CRUD operations
- No external monitoring integration (no Prometheus, no Datadog)
- No alerting on LLM failures or high token usage

### Backup
- No automated backup for SQLite database
- Database can be backed up by copying the `.db` file while the application is stopped
- No point-in-time recovery capability

### Scaling
- Single-process architecture -- cannot horizontally scale due to SQLite
- Simulation execution blocks the event loop during LLM calls -- limits concurrent users
- For production scale, would require migration to PostgreSQL and background task queue (Celery/ARQ)
