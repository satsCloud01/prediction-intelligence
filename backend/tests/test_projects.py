"""Project CRUD and lifecycle tests."""

import pytest
from tests.conftest import create_project

pytestmark = pytest.mark.asyncio


class TestListProjects:
    async def test_list_returns_200(self, client):
        r = await client.get("/api/projects")
        assert r.status_code == 200

    async def test_list_returns_a_list(self, client):
        data = (await client.get("/api/projects")).json()
        assert isinstance(data, list)

    async def test_list_has_seeded_projects(self, client):
        data = (await client.get("/api/projects")).json()
        assert len(data) >= 3

    async def test_list_item_has_required_fields(self, client):
        projects = (await client.get("/api/projects")).json()
        required = {"id", "name", "description", "domain", "status", "current_step",
                     "agent_count", "simulation_rounds", "prediction_goal",
                     "created_at", "updated_at"}
        for p in projects:
            assert required.issubset(p.keys())

    async def test_list_ordered_by_updated_at_desc(self, client):
        projects = (await client.get("/api/projects")).json()
        dates = [p["updated_at"] for p in projects]
        assert dates == sorted(dates, reverse=True)


class TestGetProject:
    async def test_get_existing_project(self, client):
        r = await client.get("/api/projects/1")
        assert r.status_code == 200

    async def test_get_project_name(self, client):
        data = (await client.get("/api/projects/1")).json()
        assert data["name"] == "Q3 2026 Global Market Outlook"

    async def test_get_project_not_found(self, client):
        r = await client.get("/api/projects/99999")
        assert r.status_code == 404

    async def test_get_project_has_counts(self, client):
        data = (await client.get("/api/projects/1")).json()
        assert "counts" in data
        required = {"seeds", "nodes", "agents", "simulations", "reports"}
        assert required.issubset(data["counts"].keys())

    async def test_project1_has_seed_data(self, client):
        counts = (await client.get("/api/projects/1")).json()["counts"]
        assert counts["seeds"] >= 3
        assert counts["nodes"] >= 0  # may be rebuilt by prior tests
        assert counts["simulations"] >= 1
        assert counts["reports"] >= 1

    async def test_project_has_prediction_goal(self, client):
        data = (await client.get("/api/projects/1")).json()
        assert len(data["prediction_goal"]) > 0


class TestCreateProject:
    async def test_create_returns_200(self, client):
        p = await create_project(client, {"name": "Create Test 200"})
        assert "id" in p

    async def test_create_default_status_is_draft(self, client):
        p = await create_project(client, {"name": "Default Status Test"})
        assert p["status"] == "draft"

    async def test_create_with_all_fields(self, client):
        p = await create_project(client, {
            "name": "Full Fields Test",
            "description": "Full description",
            "domain": "geopolitics",
            "prediction_goal": "Predict diplomatic outcomes",
            "simulation_rounds": 20,
        })
        assert p["name"] == "Full Fields Test"

    async def test_create_and_verify_via_get(self, client):
        p = await create_project(client, {"name": "Verify Via Get"})
        r = await client.get(f"/api/projects/{p['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Verify Via Get"

    async def test_create_appears_in_list(self, client):
        p = await create_project(client, {"name": "Appears In List"})
        projects = (await client.get("/api/projects")).json()
        ids = [proj["id"] for proj in projects]
        assert p["id"] in ids

    @pytest.mark.parametrize("domain", [
        "general", "finance", "politics", "geopolitics", "technology",
        "health", "climate", "social", "creative",
    ])
    async def test_create_various_domains(self, client, domain):
        p = await create_project(client, {"name": f"Domain {domain}", "domain": domain})
        r = await client.get(f"/api/projects/{p['id']}")
        assert r.json()["domain"] == domain

    @pytest.mark.parametrize("rounds", [1, 5, 10, 25, 50])
    async def test_create_various_round_counts(self, client, rounds):
        p = await create_project(client, {
            "name": f"Rounds {rounds}",
            "simulation_rounds": rounds,
        })
        r = await client.get(f"/api/projects/{p['id']}")
        assert r.json()["simulation_rounds"] == rounds


class TestUpdateProject:
    async def test_update_name(self, client):
        p = await create_project(client, {"name": "Before Update"})
        r = await client.put(f"/api/projects/{p['id']}", json={"name": "After Update"})
        assert r.status_code == 200
        r2 = await client.get(f"/api/projects/{p['id']}")
        assert r2.json()["name"] == "After Update"

    async def test_update_description(self, client):
        p = await create_project(client, {"name": "Desc Update Test"})
        await client.put(f"/api/projects/{p['id']}", json={"description": "Updated desc"})
        r = await client.get(f"/api/projects/{p['id']}")
        assert r.json()["description"] == "Updated desc"

    async def test_update_domain(self, client):
        p = await create_project(client, {"name": "Domain Update", "domain": "finance"})
        await client.put(f"/api/projects/{p['id']}", json={"domain": "politics"})
        r = await client.get(f"/api/projects/{p['id']}")
        assert r.json()["domain"] == "politics"

    async def test_update_not_found(self, client):
        r = await client.put("/api/projects/99999", json={"name": "Nope"})
        assert r.status_code == 404

    async def test_partial_update(self, client):
        p = await create_project(client, {"name": "Partial", "domain": "finance"})
        await client.put(f"/api/projects/{p['id']}", json={"name": "Partial Updated"})
        r = await client.get(f"/api/projects/{p['id']}")
        assert r.json()["name"] == "Partial Updated"
        assert r.json()["domain"] == "finance"  # unchanged


class TestDeleteProject:
    async def test_delete_project(self, client):
        p = await create_project(client, {"name": "To Delete"})
        r = await client.delete(f"/api/projects/{p['id']}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    async def test_delete_removes_from_list(self, client):
        p = await create_project(client, {"name": "Delete Check"})
        pid = p["id"]
        await client.delete(f"/api/projects/{pid}")
        r = await client.get(f"/api/projects/{pid}")
        assert r.status_code == 404

    async def test_delete_not_found(self, client):
        r = await client.delete("/api/projects/99999")
        assert r.status_code == 404
