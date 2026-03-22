from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.database import get_db
from predictor.models import (
    Project, AgentPersona, SimulationRun, SimulationEvent,
    InteractionSession, ChatMessage,
)
from predictor.llm_dispatcher import call_llm

router = APIRouter()


class StartSessionRequest(BaseModel):
    project_id: int
    agent_persona_id: int | None = None
    session_type: str = "agent"  # agent|analyst


class SendMessageRequest(BaseModel):
    session_id: int
    message: str
    provider: str = ""
    model: str = ""


@router.get("/{project_id}/sessions")
async def list_sessions(project_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(InteractionSession).where(InteractionSession.project_id == project_id)
        .order_by(InteractionSession.created_at.desc())
    )).scalars().all()
    results = []
    for s in rows:
        agent_name = None
        if s.agent_persona_id:
            agent = await db.get(AgentPersona, s.agent_persona_id)
            agent_name = agent.name if agent else None
        msg_count = len((await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == s.id)
        )).scalars().all())
        results.append({
            "id": s.id, "session_type": s.session_type,
            "agent_name": agent_name, "agent_persona_id": s.agent_persona_id,
            "message_count": msg_count, "created_at": s.created_at.isoformat(),
        })
    return results


@router.post("/sessions")
async def start_session(body: StartSessionRequest, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    session = InteractionSession(
        project_id=body.project_id,
        agent_persona_id=body.agent_persona_id,
        session_type=body.session_type,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"session_id": session.id, "session_type": session.session_type}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: int, db: AsyncSession = Depends(get_db)):
    msgs = (await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
    )).scalars().all()
    return [
        {"id": m.id, "role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
        for m in msgs
    ]


@router.post("/chat")
async def send_message(body: SendMessageRequest, x_api_key: Optional[str] = Header(None),
                        db: AsyncSession = Depends(get_db)):
    """Chat with a simulated agent or analyst post-simulation."""
    session = await db.get(InteractionSession, body.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # Save user message
    db.add(ChatMessage(session_id=session.id, role="user", content=body.message))

    # Build context
    project = await db.get(Project, session.project_id)
    persona = await db.get(AgentPersona, session.agent_persona_id) if session.agent_persona_id else None

    # Get chat history
    history = (await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.id)
    )).scalars().all()
    history_text = "\n".join(f"{m.role}: {m.content}" for m in history[-10:])

    # Get simulation context
    latest_run = (await db.execute(
        select(SimulationRun).where(SimulationRun.project_id == session.project_id)
        .order_by(SimulationRun.id.desc()).limit(1)
    )).scalars().first()

    sim_context = ""
    if latest_run:
        events = (await db.execute(
            select(SimulationEvent).where(SimulationEvent.run_id == latest_run.id)
            .order_by(SimulationEvent.round_num).limit(20)
        )).scalars().all()
        sim_context = "\n".join(f"Round {e.round_num}: {e.description}" for e in events)

    if session.session_type == "agent" and persona:
        system = f"""You are {persona.name}, a {persona.role} (age {persona.age}).
Personality: {persona.personality}
Background: {persona.background}
Beliefs: {persona.beliefs}
Goals: {persona.goals}

You participated in a prediction simulation for the project "{project.name}" with the goal: {project.prediction_goal}.

SIMULATION EVENTS YOU WITNESSED:
{sim_context}

Stay in character. Answer questions based on your persona, beliefs, and what you observed during the simulation.
Be thoughtful and detailed in your responses."""
    else:
        system = f"""You are an analysis agent for the PredictionIntelligence platform.
You help users understand the results of swarm intelligence simulations.

PROJECT: {project.name if project else 'Unknown'}
GOAL: {project.prediction_goal if project else 'Unknown'}

SIMULATION EVENTS:
{sim_context}

Provide insightful analysis of the simulation results. Be specific and reference actual events from the simulation."""

    prompt = f"""CONVERSATION HISTORY:
{history_text}

USER: {body.message}"""

    result = await call_llm(prompt, api_key=x_api_key or "", provider=body.provider, model=body.model, system=system)
    response_text = result.get("text", "I'm unable to respond right now. Please configure an LLM API key.")

    db.add(ChatMessage(session_id=session.id, role="assistant", content=response_text))
    await db.commit()

    return {"response": response_text, "llm_provider": result.get("provider", "mock")}
