"""Unit tests for the universal LLM dispatcher."""

import pytest
from predictor.llm_dispatcher import (
    call_llm, call_llm_json, detect_provider, PROVIDERS, _mock_response,
)

pytestmark = pytest.mark.asyncio


class TestProviderRegistry:
    def test_seven_providers_registered(self):
        assert len(PROVIDERS) == 7

    @pytest.mark.parametrize("pid", [
        "anthropic", "openai", "google", "mistral", "groq", "together", "ollama",
    ])
    def test_provider_has_required_keys(self, pid):
        p = PROVIDERS[pid]
        assert "name" in p
        assert "models" in p
        assert "default_model" in p
        assert "key_prefix" in p

    @pytest.mark.parametrize("pid", list(PROVIDERS.keys()))
    def test_default_model_in_models_list(self, pid):
        p = PROVIDERS[pid]
        assert p["default_model"] in p["models"]


class TestDetectProvider:
    @pytest.mark.parametrize("key,expected", [
        ("sk-ant-api03-test", "anthropic"),
        ("sk-proj-test", "openai"),
        ("sk-other-test", "openai"),
        ("gsk_test123", "groq"),
        ("AIzaSy_test", "google"),
        ("", "mock"),
    ])
    def test_detect_provider(self, key, expected):
        assert detect_provider(key) == expected

    def test_unknown_prefix_defaults_to_anthropic(self):
        assert detect_provider("xyz_unknown_key") == "anthropic"


class TestMockResponse:
    def test_entity_extraction_mock(self):
        result = _mock_response("Extract entities from this knowledge graph text")
        import json
        data = json.loads(result["text"])
        assert "entities" in data
        assert "relations" in data
        assert len(data["entities"]) > 0

    def test_persona_generation_mock(self):
        result = _mock_response("Generate diverse agent personas for this project")
        import json
        data = json.loads(result["text"])
        assert "agents" in data
        assert len(data["agents"]) == 5

    def test_simulation_mock(self):
        result = _mock_response("Simulate 10 rounds of agent interaction")
        import json
        data = json.loads(result["text"])
        assert "round_events" in data
        assert "final_consensus" in data
        assert len(data["round_events"]) > 0

    def test_report_mock(self):
        result = _mock_response("Generate a prediction report")
        import json
        data = json.loads(result["text"])
        assert "title" in data
        assert "executive_summary" in data
        assert "predictions" in data
        assert "confidence_score" in data

    def test_default_mock(self):
        result = _mock_response("some random unknown prompt")
        assert "mock response" in result["text"].lower()

    def test_mock_provider_is_mock(self):
        result = _mock_response("anything")
        assert result["provider"] == "mock"
        assert result["model"] == "mock"
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0

    def test_simulation_events_have_agents(self):
        result = _mock_response("Simulate 5 rounds of discussion between agents")
        import json
        data = json.loads(result["text"])
        events_with_agents = [e for e in data["round_events"] if e.get("agents")]
        assert len(events_with_agents) > 0

    def test_persona_agents_have_fields(self):
        result = _mock_response("Generate diverse agent personas")
        import json
        agents = json.loads(result["text"])["agents"]
        required = {"name", "role", "age", "personality", "background", "beliefs", "goals"}
        for a in agents:
            assert required.issubset(a.keys())

    def test_predictions_have_confidence(self):
        result = _mock_response("Generate prediction report with scores")
        import json
        data = json.loads(result["text"])
        for pred in data["predictions"]:
            assert 0.0 <= pred["confidence"] <= 1.0
            assert "timeframe" in pred


class TestCallLLM:
    async def test_no_key_returns_mock(self):
        result = await call_llm("test prompt")
        assert result["provider"] == "mock"

    async def test_empty_key_returns_mock(self):
        result = await call_llm("test prompt", api_key="")
        assert result["provider"] == "mock"

    async def test_mock_has_latency_zero(self):
        result = await call_llm("test prompt")
        assert result["latency_ms"] == 0

    async def test_invalid_provider_returns_mock(self):
        result = await call_llm("test", api_key="fake", provider="nonexistent")
        assert result["provider"] == "mock"

    async def test_result_has_required_fields(self):
        result = await call_llm("test prompt")
        required = {"text", "provider", "model", "input_tokens", "output_tokens", "latency_ms"}
        assert required.issubset(result.keys())


class TestCallLLMJson:
    async def test_json_parsing(self):
        result = await call_llm_json("Extract entities from this text")
        assert "parsed" in result
        assert isinstance(result["parsed"], dict)

    async def test_json_parsed_entities(self):
        result = await call_llm_json("Extract entities and build knowledge graph")
        assert "entities" in result["parsed"]

    async def test_json_parsed_agents(self):
        result = await call_llm_json("Generate diverse agent personas for prediction")
        assert "agents" in result["parsed"]

    async def test_json_parsed_simulation(self):
        result = await call_llm_json("Simulate 10 rounds of interaction")
        assert "round_events" in result["parsed"]

    async def test_json_parsed_report(self):
        result = await call_llm_json("Generate prediction report")
        assert "predictions" in result["parsed"]

    async def test_non_json_fallback(self):
        result = await call_llm_json("random prompt without keywords")
        assert "parsed" in result
        # Should still parse since mock returns text
