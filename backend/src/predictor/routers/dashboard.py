from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.database import get_db
from predictor.models import Project, AgentPersona, SimulationRun, PredictionReport, LLMUsageLog

router = APIRouter()


@router.get("")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    total_agents = (await db.execute(select(func.count(AgentPersona.id)))).scalar() or 0
    total_runs = (await db.execute(select(func.count(SimulationRun.id)))).scalar() or 0
    total_reports = (await db.execute(select(func.count(PredictionReport.id)))).scalar() or 0
    completed_runs = (await db.execute(
        select(func.count(SimulationRun.id)).where(SimulationRun.status == "completed")
    )).scalar() or 0

    # Recent projects
    projects = (await db.execute(
        select(Project).order_by(Project.updated_at.desc()).limit(5)
    )).scalars().all()

    # LLM usage stats
    total_tokens = (await db.execute(
        select(func.sum(LLMUsageLog.input_tokens + LLMUsageLog.output_tokens))
    )).scalar() or 0

    # Status distribution
    status_rows = (await db.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status)
    )).all()
    status_dist = {row[0]: row[1] for row in status_rows}

    # Domain distribution
    domain_rows = (await db.execute(
        select(Project.domain, func.count(Project.id)).group_by(Project.domain)
    )).all()
    domain_dist = {row[0]: row[1] for row in domain_rows}

    return {
        "stats": {
            "total_projects": total_projects,
            "total_agents": total_agents,
            "total_simulations": total_runs,
            "completed_simulations": completed_runs,
            "total_reports": total_reports,
            "total_tokens_used": total_tokens,
        },
        "status_distribution": status_dist,
        "domain_distribution": domain_dist,
        "recent_projects": [
            {
                "id": p.id, "name": p.name, "domain": p.domain,
                "status": p.status, "current_step": p.current_step,
                "agent_count": p.agent_count, "updated_at": p.updated_at.isoformat(),
            }
            for p in projects
        ],
    }
