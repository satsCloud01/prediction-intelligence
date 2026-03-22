"""Real multi-round simulation engine — each round is a separate LLM call."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.database import get_db
from predictor.models import Project, AgentPersona, SimulationRun, SimulationEvent, AgentMessage
from predictor.llm_dispatcher import call_llm_json

router = APIRouter()


class RunSimulationRequest(BaseModel):
    project_id: int
    rounds: int = 10
    provider: str = ""
    model: str = ""


class RunSingleRoundRequest(BaseModel):
    run_id: int
    provider: str = ""
    model: str = ""


@router.get("/{project_id}/runs")
async def list_runs(project_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(SimulationRun).where(SimulationRun.project_id == project_id).order_by(SimulationRun.id.desc())
    )).scalars().all()
    return [
        {"id": r.id, "status": r.status, "total_rounds": r.total_rounds,
         "current_round": r.current_round, "summary": r.summary,
         "started_at": r.started_at.isoformat() if r.started_at else None,
         "completed_at": r.completed_at.isoformat() if r.completed_at else None}
        for r in rows
    ]


@router.get("/runs/{run_id}")
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {
        "id": run.id, "status": run.status, "total_rounds": run.total_rounds,
        "current_round": run.current_round, "summary": run.summary,
        "project_id": run.project_id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("/runs/{run_id}/events")
async def get_events(run_id: int, db: AsyncSession = Depends(get_db)):
    events = (await db.execute(
        select(SimulationEvent).where(SimulationEvent.run_id == run_id).order_by(SimulationEvent.round_num, SimulationEvent.id)
    )).scalars().all()
    return [
        {"id": e.id, "round_num": e.round_num, "event_type": e.event_type,
         "description": e.description, "agents_involved": e.agents_involved,
         "sentiment": e.sentiment, "impact": e.impact}
        for e in events
    ]


@router.get("/runs/{run_id}/messages")
async def get_messages(run_id: int, db: AsyncSession = Depends(get_db)):
    msgs = (await db.execute(
        select(AgentMessage).where(AgentMessage.run_id == run_id).order_by(AgentMessage.round_num, AgentMessage.id)
    )).scalars().all()
    return [
        {"id": m.id, "persona_id": m.persona_id, "round_num": m.round_num,
         "content": m.content, "sentiment": m.sentiment, "target_persona_id": m.target_persona_id}
        for m in msgs
    ]


@router.post("/create")
async def create_run(body: RunSimulationRequest, db: AsyncSession = Depends(get_db)):
    """Create a simulation run without executing. Use /round to advance round-by-round."""
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    personas = (await db.execute(
        select(AgentPersona).where(AgentPersona.project_id == body.project_id)
    )).scalars().all()
    if not personas:
        raise HTTPException(400, "No agents generated yet. Complete Step 2 first.")

    run = SimulationRun(
        project_id=body.project_id, status="pending",
        total_rounds=body.rounds, current_round=0,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return {"run_id": run.id, "status": run.status, "total_rounds": run.total_rounds}


@router.post("/round")
async def run_single_round(body: RunSingleRoundRequest, x_api_key: Optional[str] = Header(None),
                            db: AsyncSession = Depends(get_db)):
    """Execute a single round of the simulation. Call repeatedly for round-by-round control."""
    run = await db.get(SimulationRun, body.run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status == "completed":
        raise HTTPException(400, "Simulation already completed")

    next_round = run.current_round + 1
    if next_round > run.total_rounds:
        raise HTTPException(400, "All rounds completed")

    # Mark running
    if run.status == "pending":
        run.status = "running"
        run.started_at = datetime.utcnow()

    personas = (await db.execute(
        select(AgentPersona).where(AgentPersona.project_id == run.project_id)
    )).scalars().all()
    agent_names = [a.name for a in personas]

    # Get previous events for context
    prev_events = (await db.execute(
        select(SimulationEvent).where(SimulationEvent.run_id == run.id).order_by(SimulationEvent.round_num)
    )).scalars().all()
    prev_context = "\n".join(
        f"Round {e.round_num} [{e.event_type}]: {e.description}" for e in prev_events[-10:]
    ) if prev_events else "This is the first round."

    project = await db.get(Project, run.project_id)
    agents_desc = "\n".join(
        f"- {a.name} ({a.role}): {a.personality}. Believes: {a.beliefs}" for a in personas
    )

    prompt = f"""You are simulating Round {next_round} of {run.total_rounds} in a swarm intelligence prediction session.

PROJECT: {project.name}
PREDICTION GOAL: {project.prediction_goal}

AGENTS:
{agents_desc}

PREVIOUS EVENTS:
{prev_context}

Simulate Round {next_round}. Generate 1-3 events for this round. Events should build on previous rounds.
Event types: interaction, opinion_shift, conflict, consensus, event.

{"This is the FINAL round — agents should work toward a conclusion." if next_round == run.total_rounds else ""}

Return JSON:
{{
  "events": [
    {{
      "type": "interaction|opinion_shift|conflict|consensus|event",
      "description": "What happened in this event",
      "agents": ["Agent Name 1", "Agent Name 2"],
      "sentiment": 0.0,
      "message": "Direct quote from the primary agent (optional)"
    }}
  ]{', "final_consensus": "Summary of what the swarm converged on"' if next_round == run.total_rounds else ''}
}}

Agent names must match exactly: {agent_names}"""

    result = await call_llm_json(prompt, api_key=x_api_key or "", provider=body.provider, model=body.model,
                                  max_tokens=2048)
    parsed = result.get("parsed", {})
    events_data = parsed.get("events", parsed.get("round_events", []))

    persona_map = {a.name: a for a in personas}
    created_events = []

    for ev in events_data:
        event = SimulationEvent(
            run_id=run.id, round_num=next_round,
            event_type=ev.get("type", "interaction"),
            description=ev.get("description", ""),
            agents_involved=ev.get("agents", []),
            sentiment=ev.get("sentiment", 0.0),
            impact=min(abs(ev.get("sentiment", 0.0)) + 0.3, 1.0),
        )
        db.add(event)
        created_events.append(event)

        msg = ev.get("message")
        if msg and ev.get("agents"):
            agent_name = ev["agents"][0]
            persona = persona_map.get(agent_name)
            if persona:
                db.add(AgentMessage(
                    persona_id=persona.id, run_id=run.id, round_num=next_round,
                    content=msg, sentiment=ev.get("sentiment", 0.0),
                ))

    run.current_round = next_round
    is_final = next_round >= run.total_rounds
    if is_final:
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.summary = parsed.get("final_consensus", f"Simulation completed after {next_round} rounds.")
        project.status = "simulated"
        project.current_step = max(project.current_step, 4)
        project.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "run_id": run.id,
        "round": next_round,
        "events_created": len(created_events),
        "status": run.status,
        "is_final": is_final,
        "consensus": run.summary if is_final else None,
        "llm_provider": result.get("provider", "mock"),
    }


@router.post("/run")
async def run_all_rounds(body: RunSimulationRequest, x_api_key: Optional[str] = Header(None),
                          db: AsyncSession = Depends(get_db)):
    """Run ALL rounds of a simulation in sequence (convenience endpoint)."""
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    personas = (await db.execute(
        select(AgentPersona).where(AgentPersona.project_id == body.project_id)
    )).scalars().all()
    if not personas:
        raise HTTPException(400, "No agents generated yet. Complete Step 2 first.")

    # Create run
    run = SimulationRun(
        project_id=body.project_id, status="running",
        total_rounds=body.rounds, current_round=0,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    total_events = 0
    for round_num in range(1, body.rounds + 1):
        result = await run_single_round(
            RunSingleRoundRequest(run_id=run.id, provider=body.provider, model=body.model),
            x_api_key=x_api_key,
            db=db,
        )
        total_events += result["events_created"]

    await db.refresh(run)
    return {
        "run_id": run.id,
        "events_created": total_events,
        "rounds_completed": run.current_round,
        "consensus": run.summary,
        "llm_provider": "mixed",
    }


@router.put("/runs/{run_id}/pause")
async def pause_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status != "running":
        raise HTTPException(400, f"Cannot pause a {run.status} run")
    run.status = "paused"
    await db.commit()
    return {"id": run.id, "status": "paused"}


@router.put("/runs/{run_id}/resume")
async def resume_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status != "paused":
        raise HTTPException(400, f"Cannot resume a {run.status} run")
    run.status = "running"
    await db.commit()
    return {"id": run.id, "status": "running"}


@router.delete("/runs/{run_id}")
async def delete_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    # Delete events and messages
    events = (await db.execute(select(SimulationEvent).where(SimulationEvent.run_id == run_id))).scalars().all()
    for e in events:
        await db.delete(e)
    msgs = (await db.execute(select(AgentMessage).where(AgentMessage.run_id == run_id))).scalars().all()
    for m in msgs:
        await db.delete(m)
    await db.delete(run)
    await db.commit()
    return {"deleted": True}
