from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.database import get_db
from predictor.models import Project, SeedDocument, KnowledgeNode, AgentPersona, SimulationRun, PredictionReport

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    domain: str = "general"
    prediction_goal: str = ""
    simulation_rounds: int = 10


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    domain: str | None = None
    prediction_goal: str | None = None
    simulation_rounds: int | None = None


@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Project).order_by(Project.updated_at.desc()))).scalars().all()
    return [
        {
            "id": p.id, "name": p.name, "description": p.description,
            "domain": p.domain, "status": p.status, "current_step": p.current_step,
            "agent_count": p.agent_count, "simulation_rounds": p.simulation_rounds,
            "prediction_goal": p.prediction_goal,
            "created_at": p.created_at.isoformat(), "updated_at": p.updated_at.isoformat(),
        }
        for p in rows
    ]


@router.post("")
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    p = Project(**body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return {"id": p.id, "name": p.name, "status": p.status}


@router.get("/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    seed_count = len((await db.execute(select(SeedDocument).where(SeedDocument.project_id == p.id))).scalars().all())
    node_count = len((await db.execute(select(KnowledgeNode).where(KnowledgeNode.project_id == p.id))).scalars().all())
    agent_count = len((await db.execute(select(AgentPersona).where(AgentPersona.project_id == p.id))).scalars().all())
    run_count = len((await db.execute(select(SimulationRun).where(SimulationRun.project_id == p.id))).scalars().all())
    report_count = len((await db.execute(select(PredictionReport).where(PredictionReport.project_id == p.id))).scalars().all())

    return {
        "id": p.id, "name": p.name, "description": p.description,
        "domain": p.domain, "prediction_goal": p.prediction_goal,
        "status": p.status, "current_step": p.current_step,
        "agent_count": p.agent_count, "simulation_rounds": p.simulation_rounds,
        "created_at": p.created_at.isoformat(), "updated_at": p.updated_at.isoformat(),
        "counts": {
            "seeds": seed_count, "nodes": node_count, "agents": agent_count,
            "simulations": run_count, "reports": report_count,
        },
    }


@router.put("/{project_id}")
async def update_project(project_id: int, body: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    await db.commit()
    return {"id": p.id, "name": p.name, "status": p.status}


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    await db.delete(p)
    await db.commit()
    return {"deleted": True}
