"""Tier-2 LLM polish (optional) · multi-provider.

Two wire formats behind one streaming interface:
  • OpenAI-compatible  (DeepSeek, OpenAI, OpenRouter, Groq, local Ollama…)
      POST {base}/chat/completions   · SSE choices[].delta.content
  • Anthropic / Claude
      POST {base}/v1/messages        · SSE content_block_delta.delta.text
      headers x-api-key + anthropic-version; NO temperature on Opus 4.x

Raw HTTP (httpx) is used for BOTH so the router stays uniform and transparent
— DeepSeek has no Anthropic SDK, and keeping one mechanism makes the provider
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

# default model per provider when the user hasn't picked one
DEFAULT_MODEL = {
    "anthropic": "claude-opus-4-8",
    "deepseek": "deepseek-chat",
    "openai": "gpt-4o-mini",
}
DEFAULT_BASE = {
    "anthropic": "https://api.anthropic.com",
    "deepseek": "https://api.deepseek.com",
    "openai": "https://api.openai.com/v1",
}

# runtime, in-process override (set via the Settings panel). None => use .env.
_store: dict = {"provider": None, "api_key": None, "base_url": None, "model": None}


def configure(provider: str | None, api_key: str | None,
              base_url: str | None, model: str | None) -> None:
    _store.update(provider=provider or None, api_key=api_key or None,
                  base_url=base_url or None, model=model or None)


def _active() -> dict:
    """Resolve the effective provider config: runtime store wins, then .env."""
    if _store["api_key"]:
        provider = _store["provider"] or "deepseek"
        return {
            "provider": provider,
            "api_key": _store["api_key"],
            "base_url": _store["base_url"] or DEFAULT_BASE[provider],
            "model": _store["model"] or DEFAULT_MODEL[provider],
        }
    if settings.llm_api_key:  # .env fallback (OpenAI-compatible)
        return {"provider": "openai", "api_key": settings.llm_api_key,
                "base_url": settings.llm_base_url, "model": settings.llm_model}
    return {}


def status() -> dict:
    cfg = _active()
    return {"enabled": bool(cfg),
            "provider": cfg.get("provider"),
            "model": cfg.get("model")}


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


def complete(prompt: str, system: str = "", max_tokens: int = 4000) -> str:
    """One-shot, non-streaming completion. Raises on failure (unlike
    polish_stream, which swallows errors for the chat UI): a caller like
    the engineering loop needs to know generation actually failed, not
    silently fall back to nothing.
    """
    cfg = _active()
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
