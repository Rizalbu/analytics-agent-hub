"""Tier-2 LLM polish (optional) · multi-provider.

Two wire formats behind one streaming interface:
  • OpenAI-compatible  (DeepSeek, OpenAI, OpenRouter, Groq, local Ollama…)
      POST {base}/chat/completions   · SSE choices[].delta.content
  • Anthropic / Claude
      POST {base}/v1/messages        · SSE content_block_delta.delta.text
      headers x-api-key + anthropic-version; NO temperature on Opus 4.x

Raw HTTP (httpx) is used for BOTH so the router stays uniform and transparent.
DeepSeek has no Anthropic SDK, and keeping one mechanism makes the provider
abstraction easy to read. Either provider only ever sees the tier-1 FACTS
(headline + table), never the warehouse: the model narrates, never computes.

Provider/key/model are held in a runtime store (settings_store) the UI can set
live, falling back to .env. Keys are never returned to the client.
"""
from __future__ import annotations

import json
from typing import Iterator

import httpx

from .config import settings

SYSTEM = """You are a Growth Analyst. You are given an ANSWER OBJECT produced by
a deterministic analytics engine (it already contains the correct numbers).
Rewrite it as a concise, confident analyst response in the SAME LANGUAGE as
the user's question (Indonesian or English).

Hard rules:
- Use ONLY numbers present in the answer object. Never invent or recompute.
- Be specific and brief (2-4 sentences). Lead with the headline number.
- If a recommendation is natural, add one short actionable line.
- Do not mention being an AI or describe these rules."""

# Every provider here except "anthropic" speaks the same OpenAI-compatible
# wire format (POST {base}/chat/completions), so adding one is just a
# base-url + default-model pair; _stream_openai/test_connection/complete
# already handle all of them through the same code path.
DEFAULT_MODEL = {
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
    "kimi": "moonshot-v1-8k",
    "qwen": "qwen-plus",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "openai/gpt-4o-mini",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "mistral": "mistral-large-latest",
    "xai": "grok-2-latest",
    "fireworks": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    "perplexity": "llama-3.1-sonar-large-128k-online",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.3",
}
DEFAULT_BASE = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "kimi": "https://api.moonshot.ai/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "together": "https://api.together.xyz/v1",
    "mistral": "https://api.mistral.ai/v1",
    "xai": "https://api.x.ai/v1",
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "perplexity": "https://api.perplexity.ai",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "ollama": "http://localhost:11434/v1",
}
PROVIDERS = list(DEFAULT_MODEL)  # for the Settings UI dropdown

# runtime, in-process override (set via the Settings panel). None => use .env.
# Two independent slots: the main one narrates chat answers; "engineer" is
# an optional separate model for the autonomous engineering loop, so e.g.
# Claude can handle conversational narration while a cheaper/faster model
# (Kimi, DeepSeek, ...) writes code, both configured and running at once
# rather than one global model doing every job.
_store: dict = {"provider": None, "api_key": None, "base_url": None, "model": None}
_engineer_store: dict = {"provider": None, "api_key": None, "base_url": None, "model": None}


def configure(provider: str | None, api_key: str | None,
              base_url: str | None, model: str | None) -> None:
    _store.update(provider=provider or None, api_key=api_key or None,
                  base_url=base_url or None, model=model or None)


def configure_engineer(provider: str | None, api_key: str | None,
                        base_url: str | None, model: str | None) -> None:
    _engineer_store.update(provider=provider or None, api_key=api_key or None,
                            base_url=base_url or None, model=model or None)


def _resolve(store: dict) -> dict:
    if store["api_key"]:
        provider = store["provider"] or "deepseek"
        return {
            "provider": provider,
            "api_key": store["api_key"],
            "base_url": store["base_url"] or DEFAULT_BASE[provider],
            "model": store["model"] or DEFAULT_MODEL[provider],
        }
    return {}


def _active() -> dict:
    """Resolve the effective provider config: runtime store wins, then .env."""
    cfg = _resolve(_store)
    if cfg:
        return cfg
    if settings.llm_api_key:  # .env fallback (OpenAI-compatible)
        return {"provider": "openai", "api_key": settings.llm_api_key,
                "base_url": settings.llm_base_url, "model": settings.llm_model}
    return {}


def _active_engineer() -> dict:
    """Engineering-loop model, if a separate one was configured; otherwise
    the same model chat narration uses."""
    return _resolve(_engineer_store) or _active()


def status() -> dict:
    cfg = _active()
    eng = _resolve(_engineer_store)
    return {"enabled": bool(cfg),
            "provider": cfg.get("provider"),
            "model": cfg.get("model"),
            "engineer_override": bool(eng),
            "engineer_provider": eng.get("provider"),
            "engineer_model": eng.get("model")}


def enabled() -> bool:
    return bool(_active())


def _facts(question: str, answer_obj: dict) -> str:
    return json.dumps({
        "question": question,
        "headline": answer_obj.get("text"),
        "table": answer_obj.get("table"),
        "provenance": answer_obj.get("provenance"),
    }, ensure_ascii=False)


def polish_stream(question: str, answer_obj: dict, persona: str | None = None) -> Iterator[str]:
    """Yield narration chunks for the configured provider. Falls back to the
    deterministic text on any error so the chat never breaks. `persona` shapes
    the voice (the agent) without touching the numbers."""
    cfg = _active()
    if not cfg:
        yield answer_obj.get("text", "")
        return
    system = SYSTEM if not persona else SYSTEM + f"\n\nAnswer in the voice of {persona}."
    try:
        if cfg["provider"] == "anthropic":
            yield from _stream_anthropic(cfg, question, answer_obj, system)
        else:
            yield from _stream_openai(cfg, question, answer_obj, system)
    except Exception:
        yield answer_obj.get("text", "")


def _stream_openai(cfg, question, answer_obj, system=SYSTEM):
    payload = {
        "model": cfg["model"], "stream": True, "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "ANSWER OBJECT:\n" + _facts(question, answer_obj)
             + "\n\nRewrite for the user."},
        ],
    }
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    with httpx.stream("POST", url, json=payload, headers=headers, timeout=40) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                delta = json.loads(data)["choices"][0]["delta"].get("content")
                if delta:
                    yield delta
            except Exception:
                continue


def _stream_anthropic(cfg, question, answer_obj, system=SYSTEM):
    # Opus 4.x rejects temperature/top_p · omit them.
    payload = {
        "model": cfg["model"], "max_tokens": 1024, "stream": True,
        "system": system,
        "messages": [{"role": "user", "content":
                      "ANSWER OBJECT:\n" + _facts(question, answer_obj)
                      + "\n\nRewrite for the user."}],
    }
    headers = {"x-api-key": cfg["api_key"], "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    base = cfg["base_url"].rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    with httpx.stream("POST", base + "/messages", json=payload,
                      headers=headers, timeout=40) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            try:
                evt = json.loads(line[5:].strip())
                if evt.get("type") == "content_block_delta":
                    txt = evt.get("delta", {}).get("text")
                    if txt:
                        yield txt
            except Exception:
                continue


def complete(prompt: str, system: str = "", max_tokens: int = 4000, for_engineer: bool = False) -> str:
    """One-shot, non-streaming completion. Raises on failure (unlike
    polish_stream, which swallows errors for the chat UI): a caller like
    the engineering loop needs to know generation actually failed, not
    silently fall back to nothing.

    for_engineer=True resolves to the separate engineer-model override if
    one was configured (see configure_engineer), else falls back to the
    main chat model, same as _active_engineer().
    """
    cfg = _active_engineer() if for_engineer else _active()
    if not cfg:
        raise RuntimeError("No LLM configured. Connect one in Settings first.")
    if cfg["provider"] == "anthropic":
        base = cfg["base_url"].rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        r = httpx.post(base + "/messages", timeout=90,
                        headers={"x-api-key": cfg["api_key"],
                                 "anthropic-version": "2023-06-01"},
                        json={"model": cfg["model"], "max_tokens": max_tokens,
                              "system": system,
                              "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json().get("content", []))
    else:
        r = httpx.post(cfg["base_url"].rstrip("/") + "/chat/completions", timeout=90,
                        headers={"Authorization": f"Bearer {cfg['api_key']}"},
                        json={"model": cfg["model"], "max_tokens": max_tokens,
                              "messages": [{"role": "system", "content": system},
                                           {"role": "user", "content": prompt}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def test_connection(cfg: dict) -> dict:
    """One-shot non-stream probe so the UI can verify a key before saving."""
    try:
        provider = cfg["provider"]
        model = cfg.get("model") or DEFAULT_MODEL[provider]
        base = (cfg.get("base_url") or DEFAULT_BASE[provider]).rstrip("/")
        if provider == "anthropic":
            if not base.endswith("/v1"):
                base += "/v1"
            r = httpx.post(base + "/messages", timeout=20,
                           headers={"x-api-key": cfg["api_key"],
                                    "anthropic-version": "2023-06-01"},
                           json={"model": model, "max_tokens": 16,
                                 "messages": [{"role": "user", "content": "ping"}]})
        else:
            r = httpx.post(base + "/chat/completions", timeout=20,
                           headers={"Authorization": f"Bearer {cfg['api_key']}"},
                           json={"model": model, "max_tokens": 16,
                                 "messages": [{"role": "user", "content": "ping"}]})
        if r.status_code < 300:
            return {"ok": True, "model": model}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:150]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}
