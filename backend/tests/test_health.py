"""Health endpoint tests."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_health_returns_200(client):
    r = await client.get("/health")
    assert r.status_code == 200


async def test_health_app_name(client):
    data = (await client.get("/health")).json()
    assert data["app"] == "PredictionIntelligence"


async def test_health_status_ok(client):
    data = (await client.get("/health")).json()
    assert data["status"] == "ok"


async def test_health_version(client):
    data = (await client.get("/health")).json()
    assert data["version"] == "1.0.0"


async def test_health_response_shape(client):
    data = (await client.get("/health")).json()
    assert {"status", "app", "version"} == set(data.keys())
