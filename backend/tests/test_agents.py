"""Agent persona generation, CRUD, and lifecycle tests."""

import pytest
from tests.conftest import create_project, add_seed, build_graph, generate_agents

pytestmark = pytest.mark.asyncio


class TestListAgents:
    async def test_list_agents_for_project1(self, client):
        r = await client.get("/api/agents/1")
        assert r.status_code == 200
        assert len(r.json()) >= 5

    async def test_agent_has_required_fields(self, client):
        agents = (await client.get("/api/agents/1")).json()
        required = {"id", "name", "role", "age", "personality", "background",
                     "beliefs", "goals", "avatar_color"}
        for a in agents:
            assert required.issubset(a.keys())

    async def test_empty_project_has_no_agents(self, client):
        p = await create_project(client, {"name": "No Agents"})
        agents = (await client.get(f"/api/agents/{p['id']}")).json()
        assert len(agents) == 0

    async def test_agent_roles_are_populated(self, client):
        agents = (await client.get("/api/agents/1")).json()
        for a in agents:
            assert len(a["role"]) > 0

    async def test_agent_names_are_unique(self, client):
        agents = (await client.get("/api/agents/1")).json()
        names = [a["name"] for a in agents]
        assert len(names) == len(set(names))


class TestGetAgentDetail:
    async def test_get_agent_detail(self, client):
        agents = (await client.get("/api/agents/1")).json()
        aid = agents[0]["id"]
        r = await client.get(f"/api/agents/detail/{aid}")
        assert r.status_code == 200

    async def test_detail_has_extended_fields(self, client):
        agents = (await client.get("/api/agents/1")).json()
        aid = agents[0]["id"]
        data = (await client.get(f"/api/agents/detail/{aid}")).json()
        assert "project_id" in data
        assert "memory" in data

    async def test_detail_not_found(self, client):
        r = await client.get("/api/agents/detail/99999")
        assert r.status_code == 404


class TestUpdateAgent:
    async def test_update_name(self, client):
        agents = (await client.get("/api/agents/1")).json()
        aid = agents[0]["id"]
        r = await client.put(f"/api/agents/detail/{aid}", json={"name": "Updated Agent Name"})
        assert r.status_code == 200
        detail = (await client.get(f"/api/agents/detail/{aid}")).json()
        assert detail["name"] == "Updated Agent Name"

    async def test_update_personality(self, client):
        agents = (await client.get("/api/agents/1")).json()
        aid = agents[1]["id"]
        await client.put(f"/api/agents/detail/{aid}", json={"personality": "Very cautious"})
        detail = (await client.get(f"/api/agents/detail/{aid}")).json()
        assert detail["personality"] == "Very cautious"

    async def test_update_not_found(self, client):
        r = await client.put("/api/agents/detail/99999", json={"name": "Nope"})
        assert r.status_code == 404

    async def test_partial_update_preserves_other_fields(self, client):
        agents = (await client.get("/api/agents/1")).json()
        aid = agents[2]["id"]
        original = (await client.get(f"/api/agents/detail/{aid}")).json()
        await client.put(f"/api/agents/detail/{aid}", json={"goals": "New goals"})
        updated = (await client.get(f"/api/agents/detail/{aid}")).json()
        assert updated["goals"] == "New goals"
        assert updated["background"] == original["background"]  # unchanged


class TestGenerateAgents:
    async def test_generate_creates_agents(self, client):
        p = await create_project(client, {"name": "Gen Agents Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        result = await generate_agents(client, p["id"], count=3)
        assert result["agents_created"] > 0

    async def test_generate_uses_mock(self, client):
        p = await create_project(client, {"name": "Gen Mock Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        result = await generate_agents(client, p["id"])
        assert result["llm_provider"] == "mock"

    async def test_generate_updates_project_status(self, client):
        p = await create_project(client, {"name": "Gen Status Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        project = (await client.get(f"/api/projects/{p['id']}")).json()
        assert project["status"] == "env_ready"
        assert project["current_step"] >= 3

    async def test_generate_project_not_found(self, client):
        r = await client.post("/api/agents/generate", json={"project_id": 99999, "count": 3})
        assert r.status_code == 404

    async def test_regenerate_replaces_agents(self, client):
        p = await create_project(client, {"name": "Regen Agents Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"], count=5)
        agents1 = (await client.get(f"/api/agents/{p['id']}")).json()
        await generate_agents(client, p["id"], count=5)
        agents2 = (await client.get(f"/api/agents/{p['id']}")).json()
        # Should be replaced, not accumulated
        assert len(agents2) == len(agents1)

    async def test_generate_updates_agent_count(self, client):
        p = await create_project(client, {"name": "Agent Count Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"], count=5)
        project = (await client.get(f"/api/projects/{p['id']}")).json()
        assert project["agent_count"] > 0


class TestDeleteAllAgents:
    async def test_delete_all_agents(self, client):
        p = await create_project(client, {"name": "Delete All Agents"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"], count=3)
        r = await client.delete(f"/api/agents/{p['id']}/all")
        assert r.status_code == 200
        agents = (await client.get(f"/api/agents/{p['id']}")).json()
        assert len(agents) == 0

    async def test_delete_all_resets_count(self, client):
        p = await create_project(client, {"name": "Delete Count Reset"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        r = await client.delete(f"/api/agents/{p['id']}/all")
        assert r.status_code == 200
        project = (await client.get(f"/api/projects/{p['id']}")).json()
        assert project["agent_count"] == 0
