"""Settings and LLM provider configuration tests."""

import pytest

pytestmark = pytest.mark.asyncio


class TestListProviders:
    async def test_list_returns_200(self, client):
        r = await client.get("/api/settings/providers")
        assert r.status_code == 200

    async def test_list_returns_seven_providers(self, client):
        providers = (await client.get("/api/settings/providers")).json()
        assert len(providers) == 7

    @pytest.mark.parametrize("provider_id", [
        "anthropic", "openai", "google", "mistral", "groq", "together", "ollama",
    ])
    async def test_provider_exists(self, client, provider_id):
        providers = (await client.get("/api/settings/providers")).json()
        ids = [p["id"] for p in providers]
        assert provider_id in ids

    async def test_provider_has_required_fields(self, client):
        providers = (await client.get("/api/settings/providers")).json()
        required = {"id", "name", "models", "default_model", "key_prefix"}
        for p in providers:
            assert required.issubset(p.keys())

    async def test_each_provider_has_models(self, client):
        providers = (await client.get("/api/settings/providers")).json()
        for p in providers:
            assert len(p["models"]) > 0

    async def test_each_provider_has_default_model(self, client):
        providers = (await client.get("/api/settings/providers")).json()
        for p in providers:
            assert p["default_model"] in p["models"]

    async def test_anthropic_models(self, client):
        providers = (await client.get("/api/settings/providers")).json()
        anthropic = next(p for p in providers if p["id"] == "anthropic")
        assert "claude-haiku-4-5-20251001" in anthropic["models"]

    async def test_openai_models(self, client):
        providers = (await client.get("/api/settings/providers")).json()
        openai = next(p for p in providers if p["id"] == "openai")
        assert "gpt-4o-mini" in openai["models"]


class TestValidateKey:
    async def test_valid_anthropic_key(self, client):
        r = await client.post("/api/settings/validate-key", json={
            "provider": "anthropic", "key": "sk-ant-api03-valid-test-key",
        })
        assert r.json()["valid"] is True

    async def test_valid_openai_key(self, client):
        r = await client.post("/api/settings/validate-key", json={
            "provider": "openai", "key": "sk-proj-valid-test-key-here",
        })
        assert r.json()["valid"] is True

    async def test_key_too_short(self, client):
        r = await client.post("/api/settings/validate-key", json={
            "provider": "anthropic", "key": "abc",
        })
        assert r.json()["valid"] is False
        assert "short" in r.json()["message"].lower()

    @pytest.mark.parametrize("provider,prefix", [
        ("anthropic", "sk-ant-"),
        ("groq", "gsk_"),
    ])
    async def test_wrong_prefix_rejected(self, client, provider, prefix):
        r = await client.post("/api/settings/validate-key", json={
            "provider": provider, "key": "wrong-prefix-key-value",
        })
        assert r.json()["valid"] is False
        assert prefix in r.json()["message"]

    async def test_empty_key_rejected(self, client):
        r = await client.post("/api/settings/validate-key", json={
            "provider": "anthropic", "key": "",
        })
        assert r.json()["valid"] is False

    @pytest.mark.parametrize("provider,key", [
        ("anthropic", "sk-ant-api03-valid-test"),
        ("openai", "sk-proj-valid-test"),
        ("groq", "gsk_valid_test_key_here"),
        ("google", "AIzaSyValid_test_key"),
    ])
    async def test_valid_prefix_accepted(self, client, provider, key):
        r = await client.post("/api/settings/validate-key", json={
            "provider": provider, "key": key,
        })
        assert r.json()["valid"] is True


class TestTestKey:
    async def test_no_key_fails(self, client):
        r = await client.post("/api/settings/test-key", json={
            "provider": "anthropic", "key": "",
        })
        assert r.json()["success"] is False
