"""Full end-to-end pipeline integration tests."""

import pytest
from tests.conftest import (
    create_project, add_seed, build_graph, generate_agents,
    run_simulation, generate_report, start_session,
)

pytestmark = pytest.mark.asyncio


class TestFullPipeline:
    async def test_complete_five_stage_pipeline(self, client):
        """Execute the full 5-stage prediction pipeline end-to-end."""
        # Stage 0: Create project
        p = await create_project(client, {
            "name": "E2E Pipeline Test",
            "domain": "finance",
            "prediction_goal": "Predict market trends",
        })
        pid = p["id"]

        # Verify initial state
        project = (await client.get(f"/api/projects/{pid}")).json()
        assert project["status"] == "draft"
        assert project["current_step"] == 1

        # Stage 1: Graph Build
        await add_seed(client, pid, {"filename": "market_data.txt"})
        await add_seed(client, pid, {"filename": "fed_minutes.txt",
                                      "content": "Federal Reserve minutes discussing inflation and rate policy."})
        result = await build_graph(client, pid)
        assert result["nodes_created"] > 0

        project = (await client.get(f"/api/projects/{pid}")).json()
        assert project["status"] == "graph_built"
        assert project["current_step"] >= 2
        assert project["counts"]["seeds"] == 2
        assert project["counts"]["nodes"] > 0

        # Stage 2: Agent Generation
        result = await generate_agents(client, pid, count=5)
        assert result["agents_created"] > 0

        project = (await client.get(f"/api/projects/{pid}")).json()
        assert project["status"] == "env_ready"
        assert project["current_step"] >= 3
        assert project["agent_count"] > 0

        agents = (await client.get(f"/api/agents/{pid}")).json()
        assert len(agents) > 0
        for a in agents:
            assert len(a["name"]) > 0
            assert len(a["role"]) > 0

        # Stage 3: Simulation
        result = await run_simulation(client, pid, rounds=5)
        assert result["events_created"] > 0
        assert len(result["consensus"]) > 0

        project = (await client.get(f"/api/projects/{pid}")).json()
        assert project["status"] == "simulated"
        assert project["current_step"] >= 4

        runs = (await client.get(f"/api/simulation/{pid}/runs")).json()
        assert len(runs) >= 1
        assert runs[0]["status"] == "completed"

        events = (await client.get(f"/api/simulation/runs/{runs[0]['id']}/events")).json()
        assert len(events) > 0

        # Stage 4: Report
        result = await generate_report(client, pid)
        assert "report_id" in result

        project = (await client.get(f"/api/projects/{pid}")).json()
        assert project["status"] == "reported"
        assert project["current_step"] >= 5

        report = (await client.get(f"/api/reports/detail/{result['report_id']}")).json()
        assert "executive_summary" in report
        assert "key_findings" in report
        assert "predictions" in report
        assert isinstance(report["predictions"], list)
        assert 0.0 <= report["confidence_score"] <= 1.0

        # Stage 5: Interaction
        agents = (await client.get(f"/api/agents/{pid}")).json()
        s = await start_session(client, pid, agent_persona_id=agents[0]["id"])
        r = await client.post("/api/interaction/chat", json={
            "session_id": s["session_id"],
            "message": "What is your prediction for the market?",
        })
        assert r.status_code == 200
        assert len(r.json()["response"]) > 0

    async def test_analyst_interaction_after_pipeline(self, client):
        """Test analyst-type interaction on project with full data."""
        s = await start_session(client, 1, session_type="analyst")
        r = await client.post("/api/interaction/chat", json={
            "session_id": s["session_id"],
            "message": "Summarize the simulation results",
        })
        assert r.status_code == 200
        assert len(r.json()["response"]) > 0


class TestSeedDataIntegrity:
    async def test_project1_fully_seeded(self, client):
        """Verify the demo project has complete pipeline data."""
        p = (await client.get("/api/projects/1")).json()
        assert p["status"] == "reported"
        assert p["counts"]["seeds"] >= 3
        assert p["counts"]["simulations"] >= 1
        assert p["counts"]["reports"] >= 1

    async def test_project2_is_draft(self, client):
        p = (await client.get("/api/projects/2")).json()
        assert p["status"] == "draft"
        assert p["current_step"] == 1

    async def test_project3_is_graph_built(self, client):
        p = (await client.get("/api/projects/3")).json()
        assert p["status"] == "graph_built"
        assert p["current_step"] == 2

    async def test_three_demo_projects_exist(self, client):
        projects = (await client.get("/api/projects")).json()
        demo_names = [p["name"] for p in projects if p["id"] <= 3]
        assert len(demo_names) >= 3

    async def test_generated_agents_have_unique_colors(self, client):
        """Generate fresh agents and verify unique colors."""
        p = await create_project(client, {"name": "Color Check"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"], count=5)
        agents = (await client.get(f"/api/agents/{p['id']}")).json()
        colors = [a["avatar_color"] for a in agents]
        assert len(set(colors)) == len(colors)

    async def test_seeded_events_cover_multiple_types(self, client):
        runs = (await client.get("/api/simulation/1/runs")).json()
        assert len(runs) > 0, "Seeded runs should exist"
        events = (await client.get(f"/api/simulation/runs/{runs[0]['id']}/events")).json()
        types = set(e["event_type"] for e in events)
        assert len(types) >= 3

    async def test_seeded_report_has_multiple_predictions(self, client):
        reports = (await client.get("/api/reports/1")).json()
        assert len(reports) > 0, "Seeded reports should exist"
        detail = (await client.get(f"/api/reports/detail/{reports[0]['id']}")).json()
        assert len(detail["predictions"]) >= 3


class TestCrossCutting:
    async def test_dashboard_reflects_new_project(self, client):
        """Creating a project should be reflected in dashboard stats."""
        before = (await client.get("/api/dashboard")).json()["stats"]["total_projects"]
        await create_project(client, {"name": "Dashboard Reflect"})
        after = (await client.get("/api/dashboard")).json()["stats"]["total_projects"]
        assert after == before + 1

    async def test_graph_build_does_not_affect_other_projects(self, client):
        """Building a graph for one project should not affect another."""
        p1 = await create_project(client, {"name": "Isolation P1"})
        p2 = await create_project(client, {"name": "Isolation P2"})
        await add_seed(client, p1["id"])
        await build_graph(client, p1["id"])
        nodes_p2 = (await client.get(f"/api/graph/{p2['id']}/nodes")).json()
        assert len(nodes_p2) == 0

    async def test_delete_project_cascades(self, client):
        """Deleting a project should remove associated seeds and agents."""
        p = await create_project(client, {"name": "Cascade Delete"})
        pid = p["id"]
        await add_seed(client, pid)
        await build_graph(client, pid)
        await generate_agents(client, pid)

        # Verify data exists
        assert len((await client.get(f"/api/graph/{pid}/seeds")).json()) > 0
        assert len((await client.get(f"/api/graph/{pid}/nodes")).json()) > 0
        assert len((await client.get(f"/api/agents/{pid}")).json()) > 0

        # Delete project
        await client.delete(f"/api/projects/{pid}")

        # Project gone
        r = await client.get(f"/api/projects/{pid}")
        assert r.status_code == 404
