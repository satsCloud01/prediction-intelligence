"""
Shared pytest fixtures for PredictionIntelligence API tests.
Uses an isolated in-memory SQLite database so tests never touch the real DB.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ── In-memory test database ─────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

import predictor.database as _db_module  # noqa: E402

_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)


async def override_get_db():
    async with _TestSession() as session:
        yield session


# Patch module-level engine/session BEFORE app is imported
_db_module.engine = _test_engine
_db_module.SessionLocal = _TestSession
_db_module.get_db = override_get_db


# ── Client fixture (session-scoped) ─────────────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def client():
    """ASGI test client with a fresh seeded in-memory database."""
    from predictor.database import Base, get_db
    from predictor.main import app

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _TestSession() as db:
        from predictor.seed import seed
        await seed(db)

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Helper: create a project via the API ─────────────────────────────────────
async def create_project(client: AsyncClient, overrides: dict | None = None) -> dict:
    payload = {
        "name": "Test Project",
        "description": "A test prediction project",
        "domain": "finance",
        "prediction_goal": "Predict test outcomes",
        "simulation_rounds": 10,
    }
    if overrides:
        payload.update(overrides)
    r = await client.post("/api/projects", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


# ── Helper: add a seed document ──────────────────────────────────────────────
async def add_seed(client: AsyncClient, project_id: int, overrides: dict | None = None) -> dict:
    payload = {
        "project_id": project_id,
        "filename": "test_doc.txt",
        "content": "The Federal Reserve announced interest rate decisions affecting global markets and inflation expectations. Tech sector shows strong growth.",
        "doc_type": "text",
    }
    if overrides:
        payload.update(overrides)
    r = await client.post("/api/graph/seeds", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


# ── Helper: build graph for a project ────────────────────────────────────────
async def build_graph(client: AsyncClient, project_id: int) -> dict:
    r = await client.post("/api/graph/build", json={"project_id": project_id})
    assert r.status_code == 200, r.text
    return r.json()


# ── Helper: generate agents for a project ────────────────────────────────────
async def generate_agents(client: AsyncClient, project_id: int, count: int = 5) -> dict:
    r = await client.post("/api/agents/generate", json={"project_id": project_id, "count": count})
    assert r.status_code == 200, r.text
    return r.json()


# ── Helper: run simulation ───────────────────────────────────────────────────
async def run_simulation(client: AsyncClient, project_id: int, rounds: int = 5) -> dict:
    r = await client.post("/api/simulation/run", json={"project_id": project_id, "rounds": rounds})
    assert r.status_code == 200, r.text
    return r.json()


# ── Helper: generate report ──────────────────────────────────────────────────
async def generate_report(client: AsyncClient, project_id: int) -> dict:
    r = await client.post("/api/reports/generate", json={"project_id": project_id})
    assert r.status_code == 200, r.text
    return r.json()


# ── Helper: start an interaction session ─────────────────────────────────────
async def start_session(client: AsyncClient, project_id: int,
                        agent_persona_id: int | None = None,
                        session_type: str = "agent") -> dict:
    payload = {"project_id": project_id, "session_type": session_type}
    if agent_persona_id:
        payload["agent_persona_id"] = agent_persona_id
    r = await client.post("/api/interaction/sessions", json=payload)
    assert r.status_code == 200, r.text
    return r.json()
