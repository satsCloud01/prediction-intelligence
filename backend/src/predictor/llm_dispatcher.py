"""Universal LLM Dispatcher — reusable multi-provider BYOK module.

Supports: Anthropic, OpenAI, Google, Mistral, Groq, Together, Ollama (local).
Keys are NEVER stored server-side — passed per-request via headers/body.
"""

import json
import re
import time
from typing import Optional

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
PROVIDERS = {
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-haiku-4-5-20251001", "claude-sonnet-4-20250514"],
        "default_model": "claude-haiku-4-5-20251001",
        "key_prefix": "sk-ant-",
    },
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-nano"],
        "default_model": "gpt-4o-mini",
        "key_prefix": "sk-",
    },
    "google": {
        "name": "Google",
        "models": ["gemini-2.0-flash", "gemini-2.5-pro"],
        "default_model": "gemini-2.0-flash",
        "key_prefix": "AI",
    },
    "mistral": {
        "name": "Mistral",
        "models": ["mistral-small-latest", "mistral-large-latest"],
        "default_model": "mistral-small-latest",
        "key_prefix": "",
    },
    "groq": {
        "name": "Groq",
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        "default_model": "llama-3.3-70b-versatile",
        "key_prefix": "gsk_",
    },
    "together": {
        "name": "Together",
        "models": ["meta-llama/Llama-3.1-70B-Instruct-Turbo", "Qwen/Qwen2.5-72B-Instruct-Turbo"],
        "default_model": "meta-llama/Llama-3.1-70B-Instruct-Turbo",
        "key_prefix": "",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "models": ["llama3.2", "mistral", "qwen2.5"],
        "default_model": "llama3.2",
        "key_prefix": "",
    },
}


def detect_provider(api_key: str) -> str:
    """Auto-detect provider from key prefix."""
    if not api_key:
        return "mock"
    if api_key.startswith("sk-ant-"):
        return "anthropic"
    if api_key.startswith("gsk_"):
        return "groq"
    if api_key.startswith("sk-"):
        return "openai"
    if api_key.startswith("AI"):
        return "google"
    return "anthropic"  # default fallback


async def call_llm(
    prompt: str,
    api_key: str = "",
    provider: str = "",
    model: str = "",
    system: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> dict:
    """Universal LLM call. Returns {text, provider, model, input_tokens, output_tokens, latency_ms}."""
    if not api_key:
        return _mock_response(prompt)

    if not provider:
        provider = detect_provider(api_key)

    if not model:
        model = PROVIDERS.get(provider, {}).get("default_model", "")

    start = time.time()
    try:
        if provider == "anthropic":
            result = await _call_anthropic(api_key, model, system, prompt, max_tokens, temperature)
        elif provider == "openai":
            result = await _call_openai(api_key, model, system, prompt, max_tokens, temperature)
        elif provider == "google":
            result = await _call_google(api_key, model, system, prompt, max_tokens, temperature)
        elif provider == "mistral":
            result = await _call_mistral(api_key, model, system, prompt, max_tokens, temperature)
        elif provider == "groq":
            result = await _call_groq(api_key, model, system, prompt, max_tokens, temperature)
        elif provider == "together":
            result = await _call_together(api_key, model, system, prompt, max_tokens, temperature)
        elif provider == "ollama":
            result = await _call_ollama(model, system, prompt, max_tokens, temperature)
        else:
            return _mock_response(prompt)
    except Exception as e:
        return {"text": f"LLM Error ({provider}): {str(e)}", "provider": provider, "model": model,
                "input_tokens": 0, "output_tokens": 0, "latency_ms": 0, "error": True}

    result["latency_ms"] = int((time.time() - start) * 1000)
    result["provider"] = provider
    result["model"] = model
    return result


async def call_llm_json(
    prompt: str,
    api_key: str = "",
    provider: str = "",
    model: str = "",
    system: str = "Respond with ONLY valid JSON, no markdown fences.",
    max_tokens: int = 2048,
) -> dict:
    """Call LLM and parse JSON from the response."""
    result = await call_llm(prompt, api_key, provider, model, system, max_tokens)
    text = result.get("text", "")
    try:
        text_clean = re.sub(r"^```(?:json)?\n?", "", text.strip())
        text_clean = re.sub(r"\n?```$", "", text_clean)
        parsed = json.loads(text_clean)
        result["parsed"] = parsed
    except json.JSONDecodeError:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            result["parsed"] = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            result["parsed"] = {"raw": text}
    return result


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------
async def _call_anthropic(api_key, model, system, prompt, max_tokens, temperature):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    kwargs = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    if temperature != 0.7:
        kwargs["temperature"] = temperature
    msg = client.messages.create(**kwargs)
    return {
        "text": msg.content[0].text,
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
    }


async def _call_openai(api_key, model, system, prompt, max_tokens, temperature):
    import openai
    client = openai.OpenAI(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
    usage = resp.usage
    return {
        "text": resp.choices[0].message.content,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }


async def _call_google(api_key, model, system, prompt, max_tokens, temperature):
    from google import genai
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = client.models.generate_content(model=model, contents=full_prompt)
    return {
        "text": response.text,
        "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if response.usage_metadata else 0,
        "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if response.usage_metadata else 0,
    }


async def _call_mistral(api_key, model, system, prompt, max_tokens, temperature):
    from mistralai import Mistral
    client = Mistral(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.complete(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
    usage = resp.usage
    return {
        "text": resp.choices[0].message.content,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }


async def _call_groq(api_key, model, system, prompt, max_tokens, temperature):
    from groq import Groq
    client = Groq(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
    usage = resp.usage
    return {
        "text": resp.choices[0].message.content,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }


async def _call_together(api_key, model, system, prompt, max_tokens, temperature):
    import httpx
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
            timeout=60,
        )
        data = resp.json()
    choice = data.get("choices", [{}])[0]
    usage = data.get("usage", {})
    return {
        "text": choice.get("message", {}).get("content", ""),
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }


async def _call_ollama(model, system, prompt, max_tokens, temperature):
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [
                    *([ {"role": "system", "content": system}] if system else []),
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            },
            timeout=120,
        )
        data = resp.json()
    return {
        "text": data.get("message", {}).get("content", ""),
        "input_tokens": data.get("prompt_eval_count", 0),
        "output_tokens": data.get("eval_count", 0),
    }


# ---------------------------------------------------------------------------
# Mock fallback
# ---------------------------------------------------------------------------
def _mock_response(prompt: str) -> dict:
    """Return a mock response when no API key is provided."""
    lower = prompt.lower()
    if ("persona" in lower and "generate" in lower) or ("agent" in lower and "diverse" in lower):
        text = json.dumps({
            "agents": [
                {"name": "Dr. Sarah Chen", "role": "economist", "age": 42, "personality": "Analytical and data-driven", "background": "PhD in macroeconomics from MIT", "beliefs": "Markets are fundamentally rational long-term", "goals": "Predict policy impacts accurately"},
                {"name": "Marcus Rivera", "role": "trader", "age": 35, "personality": "Risk-tolerant and intuitive", "background": "15 years on Wall Street", "beliefs": "Market sentiment drives short-term moves", "goals": "Identify profitable trends early"},
                {"name": "Prof. Aisha Patel", "role": "analyst", "age": 55, "personality": "Cautious and methodical", "background": "Former IMF advisor", "beliefs": "Geopolitics shapes economic outcomes", "goals": "Provide balanced risk assessments"},
                {"name": "James O'Brien", "role": "journalist", "age": 38, "personality": "Skeptical and investigative", "background": "Financial Times reporter", "beliefs": "Transparency drives market efficiency", "goals": "Uncover hidden market dynamics"},
                {"name": "Lin Wei", "role": "policy_maker", "age": 50, "personality": "Diplomatic and strategic", "background": "Central bank economist", "beliefs": "Stability is the primary objective", "goals": "Maintain economic equilibrium"},
            ]
        })
    elif "simulat" in lower and "round" in lower:
        text = json.dumps({
            "round_events": [
                {"round": 1, "type": "interaction", "description": "Dr. Chen presents inflation data showing unexpected decline", "agents": ["Dr. Sarah Chen", "Lin Wei"], "sentiment": 0.3},
                {"round": 1, "type": "opinion_shift", "description": "Marcus Rivera adjusts bullish position based on new data", "agents": ["Marcus Rivera"], "sentiment": 0.5},
                {"round": 2, "type": "conflict", "description": "Prof. Patel warns about geopolitical risks contradicting optimism", "agents": ["Prof. Aisha Patel", "Marcus Rivera"], "sentiment": -0.2},
                {"round": 2, "type": "event", "description": "Breaking news: trade agreement reached between major economies", "agents": [], "sentiment": 0.7},
                {"round": 3, "type": "consensus", "description": "Group converges on cautiously optimistic outlook", "agents": ["Dr. Sarah Chen", "Prof. Aisha Patel", "Lin Wei"], "sentiment": 0.4},
            ],
            "final_consensus": "The group reached a cautiously optimistic consensus with key risk factors acknowledged.",
        })
    elif "entity" in lower or "extract" in lower or "knowledge graph" in lower:
        text = json.dumps({
            "entities": [
                {"label": "Global Markets", "type": "concept", "description": "International financial markets and trading systems"},
                {"label": "Central Bank", "type": "organization", "description": "Monetary policy authority"},
                {"label": "Consumer Confidence", "type": "concept", "description": "Economic indicator measuring public sentiment"},
                {"label": "Tech Sector", "type": "concept", "description": "Technology industry segment"},
                {"label": "Inflation Rate", "type": "concept", "description": "Rate of price level increase"},
            ],
            "relations": [
                {"source": "Central Bank", "target": "Inflation Rate", "relation": "controls"},
                {"source": "Consumer Confidence", "target": "Global Markets", "relation": "influences"},
                {"source": "Tech Sector", "target": "Global Markets", "relation": "drives"},
            ],
        })
    elif "report" in lower or "predict" in lower:
        text = json.dumps({
            "title": "Predictive Analysis Report",
            "executive_summary": "Based on multi-agent simulation with 5 autonomous personas interacting over 10 rounds, the swarm intelligence consensus indicates a moderately positive outcome with key risk factors identified.",
            "key_findings": [
                "Strong consensus (78%) among agents on positive short-term trajectory",
                "Geopolitical risk identified as primary downside factor by 3 of 5 agents",
                "Technology sector expected to lead growth, per 4 of 5 agent perspectives",
                "Consumer confidence metrics correlate strongly with predicted outcomes",
            ],
            "predictions": [
                {"prediction": "Market will trend upward 5-8% over next quarter", "confidence": 0.72, "timeframe": "90 days"},
                {"prediction": "Central bank will maintain current rate policy", "confidence": 0.85, "timeframe": "60 days"},
                {"prediction": "Tech sector outperformance relative to broader market", "confidence": 0.68, "timeframe": "180 days"},
            ],
            "confidence_score": 0.74,
            "methodology": "Swarm intelligence simulation with 5 diverse agent personas, 10 interaction rounds, sentiment analysis, and consensus aggregation.",
        })
    else:
        text = "This is a mock response. Configure an LLM API key in Settings to enable AI-powered predictions. The platform supports Anthropic, OpenAI, Google, Mistral, Groq, Together, and Ollama."

    return {"text": text, "provider": "mock", "model": "mock", "input_tokens": 0, "output_tokens": 0, "latency_ms": 0}
