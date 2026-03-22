"""Prediction reports — full CRUD + AI generation + export."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.database import get_db
from predictor.models import Project, AgentPersona, SimulationRun, SimulationEvent, PredictionReport
from predictor.llm_dispatcher import call_llm_json

router = APIRouter()


class GenerateReportRequest(BaseModel):
    project_id: int
    run_id: int | None = None
    provider: str = ""
    model: str = ""


class ReportUpdate(BaseModel):
    title: str | None = None
    executive_summary: str | None = None
    methodology: str | None = None


@router.get("/{project_id}")
async def list_reports(project_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(PredictionReport).where(PredictionReport.project_id == project_id).order_by(PredictionReport.created_at.desc())
    )).scalars().all()
    return [
        {"id": r.id, "title": r.title, "confidence_score": r.confidence_score,
         "executive_summary": r.executive_summary[:200] if r.executive_summary else "",
         "created_at": r.created_at.isoformat()}
        for r in rows
    ]


@router.get("/detail/{report_id}")
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(PredictionReport, report_id)
    if not r:
        raise HTTPException(404, "Report not found")
    return {
        "id": r.id, "title": r.title, "executive_summary": r.executive_summary,
        "key_findings": r.key_findings, "predictions": r.predictions,
        "confidence_score": r.confidence_score, "methodology": r.methodology,
        "raw_content": r.raw_content, "created_at": r.created_at.isoformat(),
        "project_id": r.project_id,
    }


@router.put("/detail/{report_id}")
async def update_report(report_id: int, body: ReportUpdate, db: AsyncSession = Depends(get_db)):
    """Edit a report's title, summary, or methodology."""
    r = await db.get(PredictionReport, report_id)
    if not r:
        raise HTTPException(404, "Report not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(r, k, v)
    await db.commit()
    return {"id": r.id, "title": r.title}


@router.delete("/detail/{report_id}")
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(PredictionReport, report_id)
    if not r:
        raise HTTPException(404, "Report not found")
    await db.delete(r)
    await db.commit()
    return {"deleted": True}


@router.get("/detail/{report_id}/export")
async def export_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Export report as structured JSON."""
    r = await db.get(PredictionReport, report_id)
    if not r:
        raise HTTPException(404, "Report not found")
    export = {
        "report": {
            "id": r.id,
            "title": r.title,
            "generated_at": r.created_at.isoformat(),
            "confidence_score": r.confidence_score,
            "executive_summary": r.executive_summary,
            "key_findings": r.key_findings,
            "predictions": r.predictions,
            "methodology": r.methodology,
        }
    }
    return JSONResponse(
        content=export,
        headers={"Content-Disposition": f'attachment; filename="report_{report_id}.json"'},
    )


@router.post("/generate")
async def generate_report(body: GenerateReportRequest, x_api_key: Optional[str] = Header(None),
                           db: AsyncSession = Depends(get_db)):
    """Generate prediction report from simulation results."""
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    if body.run_id:
        run = await db.get(SimulationRun, body.run_id)
    else:
        run = (await db.execute(
            select(SimulationRun).where(SimulationRun.project_id == body.project_id)
            .order_by(SimulationRun.id.desc()).limit(1)
        )).scalars().first()

    if not run:
        raise HTTPException(400, "No simulation run found. Complete Step 3 first.")

    events = (await db.execute(
        select(SimulationEvent).where(SimulationEvent.run_id == run.id).order_by(SimulationEvent.round_num)
    )).scalars().all()
    personas = (await db.execute(
        select(AgentPersona).where(AgentPersona.project_id == body.project_id)
    )).scalars().all()

    events_desc = "\n".join(
        f"Round {e.round_num} [{e.event_type}] (sentiment: {e.sentiment:.1f}): {e.description}"
        for e in events
    )
    agents_desc = "\n".join(f"- {a.name} ({a.role}): {a.personality}" for a in personas)

    prompt = f"""Based on the following swarm intelligence simulation results, generate a comprehensive prediction report.

PROJECT: {p.name}
PREDICTION GOAL: {p.prediction_goal}
DOMAIN: {p.domain}

AGENTS:
{agents_desc}

SIMULATION EVENTS ({len(events)} events over {run.total_rounds} rounds):
{events_desc}

SIMULATION CONSENSUS: {run.summary}

Generate a professional prediction report with:
1. Executive summary
2. Key findings (5-7 bullet points)
3. Specific predictions with confidence scores
4. Methodology description

Return JSON:
{{
  "title": "Report title",
  "executive_summary": "2-3 paragraph executive summary",
  "key_findings": ["finding 1", "finding 2", ...],
  "predictions": [
    {{"prediction": "specific prediction", "confidence": 0.75, "timeframe": "90 days"}}
  ],
  "confidence_score": 0.74,
  "methodology": "Description of methodology used"
}}"""

    result = await call_llm_json(prompt, api_key=x_api_key or "", provider=body.provider, model=body.model,
                                  max_tokens=4096)
    parsed = result.get("parsed", {})

    report = PredictionReport(
        project_id=body.project_id,
        title=parsed.get("title", f"Prediction Report — {p.name}"),
        executive_summary=parsed.get("executive_summary", ""),
        key_findings=parsed.get("key_findings", []),
        predictions=parsed.get("predictions", []),
        confidence_score=parsed.get("confidence_score", 0.0),
        methodology=parsed.get("methodology", ""),
        raw_content=result.get("text", ""),
    )
    db.add(report)

    p.status = "reported"
    p.current_step = max(p.current_step, 5)
    p.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(report)

    return {
        "report_id": report.id,
        "title": report.title,
        "confidence_score": report.confidence_score,
        "llm_provider": result.get("provider", "mock"),
    }
