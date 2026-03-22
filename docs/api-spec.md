# PredictionIntelligence - API Specification

Base URL: `/api`

All request/response bodies are JSON. Errors return `{"detail": "<message>"}` with appropriate HTTP status.

LLM-dependent endpoints require `X-Api-Key` header with the provider API key. Provider and model are specified in the request body or project config.

---

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |

**Response**: `{"status": "healthy", "app": "PredictionIntelligence", "version": "1.0.0"}`

---

## Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard` | Dashboard summary stats |
| GET | `/api/dashboard/recent-activity` | Recent audit log entries |
| GET | `/api/dashboard/pipeline-status` | Pipeline stage counts across projects |

### GET /api/dashboard
**Response**:
```json
{
  "projects_total": 5,
  "projects_active": 3,
  "simulations_total": 12,
  "simulations_completed": 9,
  "reports_total": 8,
  "agents_total": 20,
  "nodes_total": 150,
  "edges_total": 200,
  "llm_calls_total": 450,
  "total_tokens_used": 125000
}
```

### GET /api/dashboard/recent-activity
**Query params**: `limit` (optional, default 20)
**Response**: Array of audit log entries with `entity_type`, `action`, `details`, `timestamp`.

### GET /api/dashboard/pipeline-status
**Response**:
```json
{
  "draft": 1,
  "graph_building": 0,
  "environment_setup": 1,
  "simulating": 1,
  "completed": 2
}
```

---

## Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{project_id}` | Get project with counts |
| POST | `/api/projects` | Create project |
| PUT | `/api/projects/{project_id}` | Update project |
| DELETE | `/api/projects/{project_id}` | Delete project and all children |
| POST | `/api/projects/{project_id}/documents` | Upload seed document |
| GET | `/api/projects/{project_id}/documents` | List seed documents |
| DELETE | `/api/projects/{project_id}/documents/{doc_id}` | Delete seed document |

### GET /api/projects
**Query params**: `status` (optional)
**Response**: Array of project objects with `node_count`, `agent_count`, `simulation_count`, `report_count`.

### GET /api/projects/{project_id}
**Response**: Full project object with nested counts and latest simulation status.

### POST /api/projects
**Request body**:
```json
{
  "name": "string (required)",
  "description": "string",
  "config": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514"
  }
}
```
**Response**: `{"id": 1, "name": "...", "status": "draft"}`

### PUT /api/projects/{project_id}
**Request body**: Same fields as POST, all optional. Only provided fields are updated.
**Response**: `{"id": 1, "name": "...", "status": "updated"}`

### DELETE /api/projects/{project_id}
Cascades: deletes all seed documents, nodes, edges, agents, simulations, events, messages, reports, sessions, and chat messages.
**Response**: `{"status": "deleted"}`

### POST /api/projects/{project_id}/documents
**Content-Type**: `multipart/form-data`
**Request**: File upload field `file` (text, PDF, markdown, CSV)
**Response**: `{"id": 1, "filename": "market_research.pdf", "doc_type": "pdf"}`

### GET /api/projects/{project_id}/documents
**Response**: Array of `{id, filename, doc_type, uploaded_at}` (content excluded for brevity).

### DELETE /api/projects/{project_id}/documents/{doc_id}
**Response**: `{"status": "deleted"}`

---

## Graph

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/graph/{project_id}` | Get full graph (nodes + edges) |
| POST | `/api/graph/{project_id}/extract` | Extract graph from seed documents via LLM |
| POST | `/api/graph/{project_id}/nodes` | Create node |
| PUT | `/api/graph/{project_id}/nodes/{node_id}` | Update node |
| DELETE | `/api/graph/{project_id}/nodes/{node_id}` | Delete node and connected edges |
| POST | `/api/graph/{project_id}/edges` | Create edge |
| PUT | `/api/graph/{project_id}/edges/{edge_id}` | Update edge |
| DELETE | `/api/graph/{project_id}/edges/{edge_id}` | Delete edge |

### GET /api/graph/{project_id}
**Response**:
```json
{
  "nodes": [
    {"id": 1, "label": "GDP Growth", "node_type": "factor", "properties": {}, "position_x": 100, "position_y": 200}
  ],
  "edges": [
    {"id": 1, "source_node_id": 1, "target_node_id": 2, "relationship": "influences", "weight": 0.8, "properties": {}}
  ]
}
```

### POST /api/graph/{project_id}/extract
**Headers**: `X-Api-Key: <key>` (required)
**Request body**:
```json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514"
}
```
Reads all seed documents for the project, sends to LLM for extraction, creates nodes and edges.
**Response**: `{"nodes_created": 15, "edges_created": 22, "status": "extracted"}`

### POST /api/graph/{project_id}/nodes
**Request body**:
```json
{
  "label": "string (required)",
  "node_type": "concept | entity | factor | variable | event | trend",
  "properties": {},
  "position_x": 0,
  "position_y": 0
}
```
**Response**: `{"id": 1, "label": "...", "status": "created"}`

### POST /api/graph/{project_id}/edges
**Request body**:
```json
{
  "source_node_id": 1,
  "target_node_id": 2,
  "relationship": "string",
  "weight": 0.8,
  "properties": {}
}
```
**Validation**: Returns 404 if source or target node does not exist in the project.
**Response**: `{"id": 1, "relationship": "...", "status": "created"}`

---

## Agents

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agents/{project_id}` | List agents for project |
| GET | `/api/agents/{project_id}/{agent_id}` | Get agent detail |
| POST | `/api/agents/{project_id}` | Create agent persona |
| PUT | `/api/agents/{project_id}/{agent_id}` | Update agent persona |
| DELETE | `/api/agents/{project_id}/{agent_id}` | Delete agent |
| GET | `/api/agents/gallery` | List all agent personas across projects |

### POST /api/agents/{project_id}
**Request body**:
```json
{
  "name": "string (required)",
  "role": "string",
  "personality": "string",
  "expertise": ["economics", "geopolitics"],
  "goals": ["identify emerging risks"],
  "constraints": ["must cite evidence from graph"]
}
```
**Response**: `{"id": 1, "name": "...", "status": "created"}`

### GET /api/agents/gallery
**Response**: Array of all agent personas with `project_name` included.

---

## Simulation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/simulation/{project_id}` | List simulations for project |
| GET | `/api/simulation/{project_id}/{sim_id}` | Get simulation with events and messages |
| POST | `/api/simulation/{project_id}` | Create and configure simulation |
| POST | `/api/simulation/{project_id}/{sim_id}/run` | Execute simulation (round-by-round) |
| POST | `/api/simulation/{project_id}/{sim_id}/cancel` | Cancel running simulation |
| GET | `/api/simulation/{project_id}/{sim_id}/events` | Get simulation events |
| GET | `/api/simulation/{project_id}/{sim_id}/messages` | Get agent messages |

### POST /api/simulation/{project_id}
**Request body**:
```json
{
  "rounds_total": 5,
  "config": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.7
  }
}
```
**Validation**: Requires at least 2 agents and a non-empty graph for the project.
**Response**: `{"id": 1, "status": "pending", "rounds_total": 5}`

### POST /api/simulation/{project_id}/{sim_id}/run
**Headers**: `X-Api-Key: <key>` (required)
Executes all rounds sequentially. For each round, each agent makes an LLM call with:
- Knowledge graph context
- Prior round messages
- Agent persona (role, personality, goals, constraints)

Creates SimulationEvent and AgentMessage records per round per agent.
**Response**:
```json
{
  "id": 1,
  "status": "completed",
  "rounds_completed": 5,
  "total_events": 25,
  "total_messages": 40
}
```

### GET /api/simulation/{project_id}/{sim_id}/events
**Query params**: `round_number` (optional), `agent_id` (optional)
**Response**: Array of simulation events ordered by round and timestamp.

### GET /api/simulation/{project_id}/{sim_id}/messages
**Query params**: `round_number` (optional), `sender_agent_id` (optional)
**Response**: Array of agent messages with `sender_name` and `receiver_name` resolved.

---

## Reports

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reports/{project_id}` | List reports for project |
| GET | `/api/reports/{project_id}/{report_id}` | Get full report |
| POST | `/api/reports/{project_id}` | Generate report from simulation |
| DELETE | `/api/reports/{project_id}/{report_id}` | Delete report |
| GET | `/api/reports/{project_id}/{report_id}/export` | Export report as JSON |

### POST /api/reports/{project_id}
**Headers**: `X-Api-Key: <key>` (required)
**Request body**:
```json
{
  "simulation_id": 1,
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514"
}
```
**Validation**: Simulation must be in "completed" status.
**Response**:
```json
{
  "id": 1,
  "title": "Market Disruption Prediction Report",
  "summary": "...",
  "predictions_count": 8,
  "status": "generated"
}
```

### GET /api/reports/{project_id}/{report_id}
**Response**: Full report object with `predictions` array, `confidence_scores`, `methodology`, and associated `simulation` summary.

### GET /api/reports/{project_id}/{report_id}/export
**Response**: Full report as downloadable JSON with `Content-Disposition: attachment` header.

---

## Interaction

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/interaction/sessions` | List interaction sessions |
| POST | `/api/interaction/sessions` | Start new session |
| GET | `/api/interaction/sessions/{session_id}` | Get session with chat history |
| POST | `/api/interaction/sessions/{session_id}/chat` | Send message |
| POST | `/api/interaction/sessions/{session_id}/end` | End session |

### POST /api/interaction/sessions
**Request body**: `{"report_id": 1}`
**Response**: `{"id": 1, "report_id": 1, "status": "active"}`

### GET /api/interaction/sessions/{session_id}
**Response**: Session object with `messages` array (all ChatMessage records) and `report_summary`.

### POST /api/interaction/sessions/{session_id}/chat
**Headers**: `X-Api-Key: <key>` (required)
**Request body**:
```json
{
  "message": "What are the top 3 risks identified?",
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514"
}
```
Loads report context (predictions, methodology, simulation data) and chat history. Sends to LLM with system prompt instructing contextual Q&A.
**Response**:
```json
{
  "role": "assistant",
  "content": "Based on the simulation results, the top 3 risks are...",
  "timestamp": "2026-03-22T10:30:00Z"
}
```

### POST /api/interaction/sessions/{session_id}/end
**Response**: `{"id": 1, "status": "ended"}`

---

## Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/settings` | Get all settings |
| PUT | `/api/settings` | Create/update a setting |
| GET | `/api/settings/api-key-status` | Check if API key is present in request header |
| POST | `/api/settings/test-connection` | Test LLM provider API key validity |
| GET | `/api/settings/providers` | List supported LLM providers and their models |

### PUT /api/settings
**Request body**: `{"key": "string", "value": "string"}`
Rejects any key containing "api_key" with `{"status": "rejected", "detail": "API keys must be stored client-side only."}`.
**Response**: `{"key": "...", "value": "...", "status": "saved"}`

### GET /api/settings/api-key-status
**Headers**: `X-Api-Key: <key>` (optional)
**Response**: `{"has_api_key": true}` or `{"has_api_key": false}`

### POST /api/settings/test-connection
**Headers**: `X-Api-Key: <key>` (required)
**Request body**: `{"provider": "anthropic", "model": "claude-sonnet-4-20250514"}`
Makes a real API call to the specified provider to verify the key works.
**Response**: `{"valid": true, "provider": "anthropic"}` or `{"valid": false, "error": "..."}`

### GET /api/settings/providers
**Response**:
```json
{
  "providers": [
    {"name": "anthropic", "label": "Anthropic", "models": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]},
    {"name": "openai", "label": "OpenAI", "models": ["gpt-4o", "gpt-4o-mini"]},
    {"name": "google", "label": "Google", "models": ["gemini-2.0-flash", "gemini-2.5-pro"]},
    {"name": "mistral", "label": "Mistral", "models": ["mistral-large-latest"]},
    {"name": "groq", "label": "Groq", "models": ["llama-3.3-70b-versatile"]},
    {"name": "together", "label": "Together", "models": ["meta-llama/Llama-3-70b-chat-hf"]},
    {"name": "ollama", "label": "Ollama (Local)", "models": ["llama3", "mistral"]}
  ]
}
```
