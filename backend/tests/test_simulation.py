"""Simulation run, events, messages, pause/resume, delete tests."""

import pytest
from tests.conftest import create_project, add_seed, build_graph, generate_agents, run_simulation

pytestmark = pytest.mark.asyncio


class TestListRuns:
    async def test_list_runs_for_project1(self, client):
        r = await client.get("/api/simulation/1/runs")
        assert r.status_code == 200
        assert len(r.json()) >= 1

    async def test_run_has_required_fields(self, client):
        runs = (await client.get("/api/simulation/1/runs")).json()
        required = {"id", "status", "total_rounds", "current_round", "summary"}
        for run in runs:
            assert required.issubset(run.keys())

    async def test_seeded_run_is_completed(self, client):
        runs = (await client.get("/api/simulation/1/runs")).json()
        assert runs[0]["status"] == "completed"


class TestGetRun:
    async def test_get_run_detail(self, client):
        runs = (await client.get("/api/simulation/1/runs")).json()
        r = await client.get(f"/api/simulation/runs/{runs[0]['id']}")
        assert r.status_code == 200
        assert "project_id" in r.json()

    async def test_get_run_not_found(self, client):
        r = await client.get("/api/simulation/runs/99999")
        assert r.status_code == 404


class TestGetEvents:
    async def test_get_events(self, client):
        runs = (await client.get("/api/simulation/1/runs")).json()
        r = await client.get(f"/api/simulation/runs/{runs[0]['id']}/events")
        assert r.status_code == 200
        assert len(r.json()) >= 10

    async def test_event_types_are_valid(self, client):
        runs = (await client.get("/api/simulation/1/runs")).json()
        events = (await client.get(f"/api/simulation/runs/{runs[0]['id']}/events")).json()
        valid = {"interaction", "opinion_shift", "conflict", "consensus", "event"}
        for e in events:
            assert e["event_type"] in valid


class TestCreateRun:
    async def test_create_run_pending(self, client):
        p = await create_project(client, {"name": "Create Run Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        r = await client.post("/api/simulation/create", json={"project_id": p["id"], "rounds": 5})
        assert r.status_code == 200
        assert r.json()["status"] == "pending"
        assert r.json()["total_rounds"] == 5

    async def test_create_run_no_agents(self, client):
        p = await create_project(client, {"name": "No Agent Create"})
        r = await client.post("/api/simulation/create", json={"project_id": p["id"]})
        assert r.status_code == 400


class TestRoundByRound:
    async def test_run_single_round(self, client):
        p = await create_project(client, {"name": "Single Round Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        run = (await client.post("/api/simulation/create", json={"project_id": p["id"], "rounds": 3})).json()
        r = await client.post("/api/simulation/round", json={"run_id": run["run_id"]})
        assert r.status_code == 200
        assert r.json()["round"] == 1
        assert r.json()["events_created"] > 0
        assert r.json()["is_final"] is False

    async def test_run_until_completion(self, client):
        p = await create_project(client, {"name": "Complete Rounds"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        run = (await client.post("/api/simulation/create", json={"project_id": p["id"], "rounds": 2})).json()
        r1 = await client.post("/api/simulation/round", json={"run_id": run["run_id"]})
        assert r1.json()["is_final"] is False
        r2 = await client.post("/api/simulation/round", json={"run_id": run["run_id"]})
        assert r2.json()["is_final"] is True
        assert r2.json()["consensus"] is not None

    async def test_cannot_exceed_total_rounds(self, client):
        p = await create_project(client, {"name": "Exceed Rounds"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        run = (await client.post("/api/simulation/create", json={"project_id": p["id"], "rounds": 1})).json()
        await client.post("/api/simulation/round", json={"run_id": run["run_id"]})
        r = await client.post("/api/simulation/round", json={"run_id": run["run_id"]})
        assert r.status_code == 400

    async def test_round_not_found(self, client):
        r = await client.post("/api/simulation/round", json={"run_id": 99999})
        assert r.status_code == 404


class TestRunAll:
    async def test_run_all_creates_events(self, client):
        p = await create_project(client, {"name": "Run All Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        result = await run_simulation(client, p["id"], rounds=3)
        assert result["events_created"] > 0

    async def test_run_all_no_agents(self, client):
        p = await create_project(client, {"name": "Run All No Agents"})
        r = await client.post("/api/simulation/run", json={"project_id": p["id"]})
        assert r.status_code == 400


class TestPauseResume:
    async def test_pause_running(self, client):
        p = await create_project(client, {"name": "Pause Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        run = (await client.post("/api/simulation/create", json={"project_id": p["id"], "rounds": 5})).json()
        await client.post("/api/simulation/round", json={"run_id": run["run_id"]})
        r = await client.put(f"/api/simulation/runs/{run['run_id']}/pause")
        assert r.status_code == 200
        assert r.json()["status"] == "paused"

    async def test_resume_paused(self, client):
        p = await create_project(client, {"name": "Resume Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        run = (await client.post("/api/simulation/create", json={"project_id": p["id"], "rounds": 5})).json()
        await client.post("/api/simulation/round", json={"run_id": run["run_id"]})
        await client.put(f"/api/simulation/runs/{run['run_id']}/pause")
        r = await client.put(f"/api/simulation/runs/{run['run_id']}/resume")
        assert r.status_code == 200
        assert r.json()["status"] == "running"

    async def test_cannot_pause_pending(self, client):
        p = await create_project(client, {"name": "Pause Pending"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        run = (await client.post("/api/simulation/create", json={"project_id": p["id"], "rounds": 5})).json()
        r = await client.put(f"/api/simulation/runs/{run['run_id']}/pause")
        assert r.status_code == 400

    async def test_pause_not_found(self, client):
        r = await client.put("/api/simulation/runs/99999/pause")
        assert r.status_code == 404


class TestDeleteRun:
    async def test_delete_run(self, client):
        p = await create_project(client, {"name": "Delete Run"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        result = await run_simulation(client, p["id"], rounds=2)
        r = await client.delete(f"/api/simulation/runs/{result['run_id']}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    async def test_delete_run_not_found(self, client):
        r = await client.delete("/api/simulation/runs/99999")
        assert r.status_code == 404
