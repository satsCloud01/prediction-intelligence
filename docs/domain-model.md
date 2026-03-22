# PredictionIntelligence - Domain Model

## Entity Relationship Overview

```
Project ----< SeedDocument
  |
  +----< KnowledgeNode ----< KnowledgeEdge (source_node_id + target_node_id)
  |
  +----< AgentPersona
  |
  +----< SimulationRun ----< SimulationEvent (via simulation_id + agent_id)
              |
              +----< AgentMessage (via simulation_id + sender/receiver agent_id)
              |
              +----< PredictionReport ----< InteractionSession ----< ChatMessage

AuditLog (standalone - references any entity by type + id)
LLMUsageLog (standalone - tracks all LLM API calls)
```

---

## Entities

### Project
A prediction project that contains the full pipeline: seed documents, knowledge graph, agents, simulations, and reports.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| name | String(300) | Not null | Project name |
| description | Text | Default "" | Project description |
| status | String(50) | Default "draft" | draft, graph_building, environment_setup, simulating, completed |
| config | JSON | Default {} | Project-level configuration (provider, model, etc.) |
| created_at | DateTime | UTC default | Creation timestamp |
| updated_at | DateTime | UTC default | Last update timestamp |

**Relationships**: One-to-many with SeedDocument, KnowledgeNode, KnowledgeEdge, AgentPersona, SimulationRun

---

### SeedDocument
A document uploaded by the user as input for knowledge graph extraction.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| project_id | Integer | FK -> projects, not null | Parent project |
| filename | String(500) | Not null | Original filename |
| content | Text | Default "" | Extracted text content |
| doc_type | String(50) | Default "text" | text, pdf, markdown, csv |
| uploaded_at | DateTime | UTC default | Upload timestamp |
| created_at | DateTime | UTC default | Creation timestamp |

---

### KnowledgeNode
A node in the knowledge graph representing a concept, entity, factor, or variable extracted from seed documents.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| project_id | Integer | FK -> projects, not null | Parent project |
| label | String(300) | Not null | Display label |
| node_type | String(100) | Default "concept" | concept, entity, factor, variable, event, trend |
| properties | JSON | Default {} | Arbitrary key-value properties |
| position_x | Float | Default 0 | X coordinate for React Flow canvas |
| position_y | Float | Default 0 | Y coordinate for React Flow canvas |
| created_at | DateTime | UTC default | Creation timestamp |

**Domain rules**:
- Node labels should be unique within a project
- Positions are persisted so the graph layout is preserved across sessions

---

### KnowledgeEdge
A directed edge in the knowledge graph representing a relationship between two nodes.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| project_id | Integer | FK -> projects, not null | Parent project |
| source_node_id | Integer | FK -> knowledge_nodes, not null | Source node |
| target_node_id | Integer | FK -> knowledge_nodes, not null | Target node |
| relationship | String(200) | Default "" | Relationship label (e.g., "causes", "influences", "depends_on") |
| weight | Float | Default 1.0 | Edge weight / strength (0.0 - 1.0) |
| properties | JSON | Default {} | Arbitrary key-value properties |
| created_at | DateTime | UTC default | Creation timestamp |

**Domain rules**:
- Self-loops (source == target) are allowed but discouraged
- Multiple edges between the same pair of nodes are allowed (different relationship types)

---

### AgentPersona
An AI agent persona configured for simulation. Each agent has a role, personality, expertise areas, and goals that shape its reasoning during simulation rounds.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| project_id | Integer | FK -> projects, not null | Parent project |
| name | String(300) | Not null | Agent display name |
| role | String(200) | Default "" | Agent role (e.g., "Economist", "Risk Analyst", "Domain Expert") |
| personality | Text | Default "" | Personality description guiding LLM behavior |
| expertise | JSON | Default [] | List of expertise area strings |
| goals | JSON | Default [] | List of goal strings the agent pursues |
| constraints | JSON | Default [] | List of constraints on agent behavior |
| created_at | DateTime | UTC default | Creation timestamp |

**Domain rules**:
- A project should have at least 2 agents for meaningful simulation
- Agent names must be unique within a project

---

### SimulationRun
A simulation execution record tracking multi-round agent interactions over the knowledge graph.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| project_id | Integer | FK -> projects, not null | Parent project |
| status | String(50) | Default "pending" | pending, running, completed, failed, cancelled |
| rounds_total | Integer | Default 3 | Total number of rounds configured |
| rounds_completed | Integer | Default 0 | Rounds completed so far |
| config | JSON | Default {} | Simulation config (provider, model, temperature, etc.) |
| started_at | DateTime | Nullable | When simulation started executing |
| completed_at | DateTime | Nullable | When simulation finished |
| created_at | DateTime | UTC default | Creation timestamp |

**Domain rules**:
- Only one simulation can be "running" per project at a time
- rounds_completed <= rounds_total
- Status transitions: pending -> running -> completed/failed

---

### SimulationEvent
A discrete event that occurred during a simulation round (agent action, observation, prediction, or state change).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| simulation_id | Integer | FK -> simulation_runs, not null | Parent simulation |
| round_number | Integer | Not null | Round in which this event occurred (1-based) |
| agent_id | Integer | FK -> agent_personas, not null | Agent that produced this event |
| event_type | String(50) | Default "observation" | observation, prediction, action, state_change, disagreement |
| content | JSON | Default {} | Event payload (varies by event_type) |
| timestamp | DateTime | UTC default | Event timestamp |

---

### AgentMessage
A message exchanged between agents during a simulation round. Captures reasoning and inter-agent communication.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| simulation_id | Integer | FK -> simulation_runs, not null | Parent simulation |
| round_number | Integer | Not null | Round number (1-based) |
| sender_agent_id | Integer | FK -> agent_personas, not null | Agent that sent the message |
| receiver_agent_id | Integer | FK -> agent_personas, nullable | Target agent (null = broadcast to all) |
| message_type | String(50) | Default "reasoning" | reasoning, challenge, agreement, proposal, rebuttal |
| content | Text | Default "" | Message content |
| reasoning | Text | Default "" | Internal reasoning chain (visible in report) |
| created_at | DateTime | UTC default | Creation timestamp |

---

### PredictionReport
A synthesized report generated from simulation results, containing predictions with confidence scores.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| simulation_id | Integer | FK -> simulation_runs, not null | Source simulation |
| title | String(500) | Default "" | Report title |
| summary | Text | Default "" | Executive summary |
| predictions | JSON | Default [] | Array of prediction objects (prediction, rationale, timeframe, impact) |
| confidence_scores | JSON | Default {} | Dict mapping prediction keys to confidence scores (0-100) |
| methodology | Text | Default "" | Description of simulation methodology used |
| generated_at | DateTime | UTC default | When the report was generated |
| created_at | DateTime | UTC default | Creation timestamp |

**Domain rules**:
- One report per simulation run (can be regenerated, replacing the previous)
- Confidence scores range from 0 to 100

---

### InteractionSession
An interactive Q&A session where users explore a completed prediction report through conversation.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| report_id | Integer | FK -> prediction_reports, not null | Associated report |
| status | String(50) | Default "active" | active, ended |
| started_at | DateTime | UTC default | Session start time |
| ended_at | DateTime | Nullable | Session end time |
| created_at | DateTime | UTC default | Creation timestamp |

---

### ChatMessage
A single message in an interaction session (either user question or assistant response).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| session_id | Integer | FK -> interaction_sessions, not null | Parent session |
| role | String(20) | Not null | "user" or "assistant" |
| content | Text | Default "" | Message content |
| timestamp | DateTime | UTC default | Message timestamp |

---

### AuditLog
A standalone audit trail recording all significant actions across the platform.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| entity_type | String(100) | Default "" | Type of entity affected (project, node, agent, simulation, etc.) |
| entity_id | Integer | Nullable | ID of the affected entity |
| action | String(50) | Default "" | Action performed (create, update, delete, run, export) |
| details | JSON | Default {} | Additional context about the action |
| timestamp | DateTime | UTC default | When the action occurred |

---

### LLMUsageLog
Tracks every LLM API call for cost monitoring and debugging.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | Integer | PK, auto | Primary key |
| provider | String(50) | Default "" | Provider name (anthropic, openai, google, etc.) |
| model | String(100) | Default "" | Model identifier used |
| prompt_tokens | Integer | Default 0 | Input token count |
| completion_tokens | Integer | Default 0 | Output token count |
| total_tokens | Integer | Default 0 | Total tokens consumed |
| latency_ms | Integer | Default 0 | Response latency in milliseconds |
| endpoint | String(200) | Default "" | Which pipeline stage or API endpoint triggered the call |
| timestamp | DateTime | UTC default | When the call was made |

**Domain rules**:
- Token counts may be approximate for providers that do not return exact counts
- Ollama calls report 0 tokens (local, no billing)
