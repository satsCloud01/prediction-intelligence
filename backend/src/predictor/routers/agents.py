"""Agent personas — full CRUD + AI generation."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.database import get_db
from predictor.models import Project, KnowledgeNode, AgentPersona
from predictor.llm_dispatcher import call_llm_json

router = APIRouter()


class AgentCreate(BaseModel):
    project_id: int
    name: str
    role: str = "analyst"
    age: int = 30
    personality: str = ""
    background: str = ""
    beliefs: str = ""
    goals: str = ""
    avatar_color: str = "#06b6d4"


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    age: int | None = None
    personality: str | None = None
    background: str | None = None
    beliefs: str | None = None
    goals: str | None = None
    avatar_color: str | None = None


class GenerateAgentsRequest(BaseModel):
    project_id: int
    count: int = 5
    provider: str = ""
    model: str = ""


@router.get("/{project_id}")
async def list_agents(project_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(AgentPersona).where(AgentPersona.project_id == project_id)
    )).scalars().all()
    return [
        {"id": a.id, "name": a.name, "role": a.role, "age": a.age,
         "personality": a.personality, "background": a.background,
         "beliefs": a.beliefs, "goals": a.goals, "avatar_color": a.avatar_color}
        for a in rows
    ]


@router.post("")
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Manually create a single agent persona."""
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    agent = AgentPersona(**body.model_dump())
    db.add(agent)
    p.agent_count = len((await db.execute(
        select(AgentPersona).where(AgentPersona.project_id == body.project_id)
    )).scalars().all()) + 1
    if p.current_step < 3 and p.status in ("graph_built", "env_ready"):
        p.status = "env_ready"
        p.current_step = max(p.current_step, 3)
    p.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(agent)
    return {"id": agent.id, "name": agent.name, "role": agent.role}


@router.get("/detail/{agent_id}")
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    a = await db.get(AgentPersona, agent_id)
    if not a:
        raise HTTPException(404, "Agent not found")
    return {
        "id": a.id, "name": a.name, "role": a.role, "age": a.age,
        "personality": a.personality, "background": a.background,
        "beliefs": a.beliefs, "goals": a.goals, "avatar_color": a.avatar_color,
        "memory": a.memory, "project_id": a.project_id,
    }


@router.put("/detail/{agent_id}")
async def update_agent(agent_id: int, body: AgentUpdate, db: AsyncSession = Depends(get_db)):
    a = await db.get(AgentPersona, agent_id)
    if not a:
        raise HTTPException(404, "Agent not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(a, k, v)
    await db.commit()
    return {"id": a.id, "name": a.name}


@router.delete("/detail/{agent_id}")
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a single agent persona."""
    a = await db.get(AgentPersona, agent_id)
    if not a:
        raise HTTPException(404, "Agent not found")
    project_id = a.project_id
    await db.delete(a)
    # Update count
    p = await db.get(Project, project_id)
    if p:
        remaining = len((await db.execute(
            select(AgentPersona).where(AgentPersona.project_id == project_id)
        )).scalars().all())
        p.agent_count = remaining
        p.updated_at = datetime.utcnow()
    await db.commit()
    return {"deleted": True}


@router.post("/generate")
async def generate_agents(body: GenerateAgentsRequest, x_api_key: Optional[str] = Header(None),
                           db: AsyncSession = Depends(get_db)):
    """Generate agent personas from knowledge graph using LLM."""
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    nodes = (await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.project_id == body.project_id)
    )).scalars().all()

    entities_desc = "\n".join(f"- {n.label} ({n.entity_type}): {n.description}" for n in nodes) if nodes else "No entities yet."

    prompt = f"""Based on the following knowledge graph entities from a prediction project, generate {body.count} diverse autonomous agent personas that will participate in a swarm intelligence simulation.

PROJECT: {p.name}
PREDICTION GOAL: {p.prediction_goal}
DOMAIN: {p.domain}

KNOWLEDGE GRAPH ENTITIES:
{entities_desc}

Generate agents with DIVERSE perspectives, backgrounds, and biases relevant to the domain.
Each agent should have a unique viewpoint that contributes to the prediction.

Return JSON:
{{
  "agents": [
    {{
      "name": "Full Name",
      "role": "role_type (e.g., economist, analyst, citizen, journalist, policy_maker, activist, researcher)",
      "age": 30,
      "personality": "2-3 sentence personality description",
      "background": "Professional and personal background",
      "beliefs": "Core beliefs that influence their predictions",
      "goals": "What they want to achieve or predict"
    }}
  ]
}}"""

    result = await call_llm_json(prompt, api_key=x_api_key or "", provider=body.provider, model=body.model)
    parsed = result.get("parsed", {})
    agents_data = parsed.get("agents", [])

    colors = ["#06b6d4", "#8b5cf6", "#f59e0b", "#ef4444", "#10b981", "#ec4899", "#3b82f6", "#f97316"]

    # Clear existing agents
    old = (await db.execute(select(AgentPersona).where(AgentPersona.project_id == body.project_id))).scalars().all()
    for a in old:
        await db.delete(a)
    await db.flush()

    created = []
    for i, ad in enumerate(agents_data):
        agent = AgentPersona(
            project_id=body.project_id,
            name=ad.get("name", f"Agent {i+1}"),
            role=ad.get("role", "analyst"),
            age=ad.get("age", 30),
            personality=ad.get("personality", ""),
            background=ad.get("background", ""),
            beliefs=ad.get("beliefs", ""),
            goals=ad.get("goals", ""),
            avatar_color=colors[i % len(colors)],
        )
        db.add(agent)
        created.append(agent)

    p.agent_count = len(created)
    p.status = "env_ready"
    p.current_step = max(p.current_step, 3)
    p.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "agents_created": len(created),
        "llm_provider": result.get("provider", "mock"),
    }


@router.delete("/{project_id}/all")
async def delete_all_agents(project_id: int, db: AsyncSession = Depends(get_db)):
    agents = (await db.execute(select(AgentPersona).where(AgentPersona.project_id == project_id))).scalars().all()
    for a in agents:
        await db.delete(a)
    p = await db.get(Project, project_id)
    if p:
        p.agent_count = 0
    await db.commit()
    return {"deleted": len(agents)}
