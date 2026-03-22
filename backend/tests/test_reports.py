"""Prediction report CRUD, generation, and export tests."""

import pytest
from tests.conftest import (
    create_project, add_seed, build_graph, generate_agents,
    run_simulation, generate_report,
)

pytestmark = pytest.mark.asyncio


class TestListReports:
    async def test_list_reports_for_project1(self, client):
        r = await client.get("/api/reports/1")
        assert r.status_code == 200
        assert len(r.json()) >= 1

    async def test_empty_project_has_no_reports(self, client):
        p = await create_project(client, {"name": "No Reports"})
        reports = (await client.get(f"/api/reports/{p['id']}")).json()
        assert len(reports) == 0


class TestGetReportDetail:
    async def test_get_seeded_report(self, client):
        reports = (await client.get("/api/reports/1")).json()
        rid = reports[0]["id"]
        r = await client.get(f"/api/reports/detail/{rid}")
        assert r.status_code == 200

    async def test_detail_has_required_fields(self, client):
        reports = (await client.get("/api/reports/1")).json()
        data = (await client.get(f"/api/reports/detail/{reports[0]['id']}")).json()
        required = {"id", "title", "executive_summary", "key_findings", "predictions",
                     "confidence_score", "methodology", "raw_content", "created_at", "project_id"}
        assert required.issubset(data.keys())

    async def test_report_not_found(self, client):
        r = await client.get("/api/reports/detail/99999")
        assert r.status_code == 404


class TestUpdateReport:
    async def test_update_title(self, client):
        reports = (await client.get("/api/reports/1")).json()
        rid = reports[0]["id"]
        r = await client.put(f"/api/reports/detail/{rid}", json={"title": "Updated Title"})
        assert r.status_code == 200
        detail = (await client.get(f"/api/reports/detail/{rid}")).json()
        assert detail["title"] == "Updated Title"

    async def test_update_summary(self, client):
        reports = (await client.get("/api/reports/1")).json()
        rid = reports[0]["id"]
        await client.put(f"/api/reports/detail/{rid}", json={"executive_summary": "New summary text"})
        detail = (await client.get(f"/api/reports/detail/{rid}")).json()
        assert detail["executive_summary"] == "New summary text"

    async def test_update_methodology(self, client):
        reports = (await client.get("/api/reports/1")).json()
        rid = reports[0]["id"]
        await client.put(f"/api/reports/detail/{rid}", json={"methodology": "New methodology"})
        detail = (await client.get(f"/api/reports/detail/{rid}")).json()
        assert detail["methodology"] == "New methodology"

    async def test_update_not_found(self, client):
        r = await client.put("/api/reports/detail/99999", json={"title": "X"})
        assert r.status_code == 404


class TestDeleteReport:
    async def test_delete_report(self, client):
        result = await generate_report(client, 1)
        r = await client.delete(f"/api/reports/detail/{result['report_id']}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    async def test_delete_report_not_found(self, client):
        r = await client.delete("/api/reports/detail/99999")
        assert r.status_code == 404


class TestExportReport:
    async def test_export_json(self, client):
        reports = (await client.get("/api/reports/1")).json()
        rid = reports[0]["id"]
        r = await client.get(f"/api/reports/detail/{rid}/export")
        assert r.status_code == 200
        data = r.json()
        assert "report" in data
        assert "title" in data["report"]
        assert "predictions" in data["report"]

    async def test_export_not_found(self, client):
        r = await client.get("/api/reports/detail/99999/export")
        assert r.status_code == 404


class TestGenerateReport:
    async def test_generate_from_seeded_project(self, client):
        result = await generate_report(client, 1)
        assert "report_id" in result

    async def test_generate_no_simulation_returns_400(self, client):
        p = await create_project(client, {"name": "No Sim Report"})
        r = await client.post("/api/reports/generate", json={"project_id": p["id"]})
        assert r.status_code == 400

    async def test_generate_project_not_found(self, client):
        r = await client.post("/api/reports/generate", json={"project_id": 99999})
        assert r.status_code == 404

    async def test_generated_report_retrievable(self, client):
        result = await generate_report(client, 1)
        r = await client.get(f"/api/reports/detail/{result['report_id']}")
        assert r.status_code == 200
