from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from predictor.database import init_db, SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with SessionLocal() as db:
        from predictor.seed import seed
        await seed(db)
    yield


app = FastAPI(
    title="PredictionIntelligence API",
    description="Swarm Intelligence Prediction Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5180", "http://localhost:5183", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from predictor.routers import dashboard, projects, graph, agents, simulation, reports, interaction, settings  # noqa: E402

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(interaction.router, prefix="/api/interaction", tags=["interaction"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": "PredictionIntelligence", "version": "1.0.0"}


# Mount static frontend in production (Docker builds copy dist/ to /app/static/)
from predictor.static_mount import mount_static  # noqa: E402
mount_static(app)
