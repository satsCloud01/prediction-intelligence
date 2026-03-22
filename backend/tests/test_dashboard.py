"""Dashboard endpoint tests."""

import pytest

pytestmark = pytest.mark.asyncio


class TestDashboardStats:
    async def test_returns_200(self, client):
        r = await client.get("/api/dashboard")
        assert r.status_code == 200

    async def test_has_stats_section(self, client):
        data = (await client.get("/api/dashboard")).json()
        assert "stats" in data

    async def test_stats_has_required_fields(self, client):
        stats = (await client.get("/api/dashboard")).json()["stats"]
        required = {
            "total_projects", "total_agents", "total_simulations",
            "completed_simulations", "total_reports", "total_tokens_used",
        }
        assert required.issubset(stats.keys())

    async def test_total_projects_from_seed(self, client):
        stats = (await client.get("/api/dashboard")).json()["stats"]
        assert stats["total_projects"] >= 3

    async def test_total_agents_from_seed(self, client):
        stats = (await client.get("/api/dashboard")).json()["stats"]
        assert stats["total_agents"] >= 5

    async def test_completed_simulations(self, client):
        stats = (await client.get("/api/dashboard")).json()["stats"]
        assert stats["completed_simulations"] >= 1

    async def test_tokens_used_is_numeric(self, client):
        stats = (await client.get("/api/dashboard")).json()["stats"]
        assert isinstance(stats["total_tokens_used"], (int, float))


class TestDashboardDistributions:
    async def test_status_distribution_is_dict(self, client):
        data = (await client.get("/api/dashboard")).json()
        assert isinstance(data["status_distribution"], dict)

    async def test_domain_distribution_is_dict(self, client):
        data = (await client.get("/api/dashboard")).json()
        assert isinstance(data["domain_distribution"], dict)

    async def test_status_distribution_has_reported(self, client):
        dist = (await client.get("/api/dashboard")).json()["status_distribution"]
        assert "reported" in dist

    async def test_domain_distribution_has_finance(self, client):
        dist = (await client.get("/api/dashboard")).json()["domain_distribution"]
        assert "finance" in dist


class TestDashboardRecentProjects:
    async def test_recent_projects_exists(self, client):
        data = (await client.get("/api/dashboard")).json()
        assert "recent_projects" in data

    async def test_recent_projects_is_list(self, client):
        data = (await client.get("/api/dashboard")).json()
        assert isinstance(data["recent_projects"], list)

    async def test_recent_projects_not_empty(self, client):
        data = (await client.get("/api/dashboard")).json()
        assert len(data["recent_projects"]) > 0

    async def test_recent_project_has_required_fields(self, client):
        projects = (await client.get("/api/dashboard")).json()["recent_projects"]
        required = {"id", "name", "domain", "status", "current_step", "agent_count", "updated_at"}
        for p in projects:
            assert required.issubset(p.keys())

    async def test_recent_projects_max_five(self, client):
        data = (await client.get("/api/dashboard")).json()
        assert len(data["recent_projects"]) <= 5
