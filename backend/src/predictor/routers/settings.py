from fastapi import APIRouter
from predictor.llm_dispatcher import PROVIDERS

router = APIRouter()


@router.get("/providers")
async def list_providers():
    """Return available LLM providers and their models."""
    return [
        {
            "id": pid,
            "name": info["name"],
            "models": info["models"],
            "default_model": info["default_model"],
            "key_prefix": info["key_prefix"],
        }
        for pid, info in PROVIDERS.items()
    ]


@router.post("/validate-key")
async def validate_key(body: dict):
    """Basic key format validation (no API call)."""
    provider = body.get("provider", "")
    key = body.get("key", "")
    if not key or len(key) < 5:
        return {"valid": False, "message": "Key too short"}
    expected = PROVIDERS.get(provider, {}).get("key_prefix", "")
    if expected and not key.startswith(expected):
        return {"valid": False, "message": f"Key should start with '{expected}' for {provider}"}
    return {"valid": True, "message": f"Key format valid for {provider}"}


@router.post("/test-key")
async def test_key(body: dict):
    """Test an API key by making a minimal LLM call."""
    from predictor.llm_dispatcher import call_llm
    provider = body.get("provider", "")
    key = body.get("key", "")
    model = body.get("model", "")
    if not key:
        return {"success": False, "message": "No key provided"}
    result = await call_llm("Say 'hello' in one word.", api_key=key, provider=provider, model=model, max_tokens=10)
    if result.get("error"):
        return {"success": False, "message": result.get("text", "Unknown error")}
    return {
        "success": True,
        "message": f"Key works! Response: {result.get('text', '')[:50]}",
        "provider": result.get("provider"),
        "model": result.get("model"),
        "latency_ms": result.get("latency_ms"),
    }
