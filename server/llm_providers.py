"""Defaults y mapeo de mensajes por proveedor LLM."""

from __future__ import annotations

from typing import Any

PROVIDERS = frozenset({"ollama", "openai", "claude", "gemini", "openai_compat"})

DEFAULTS: dict[str, dict[str, str]] = {
    "ollama": {
        "label": "Ollama (local)",
        "ollama_url": "http://127.0.0.1:11434/api/chat",
        "api_base": "",
        "model": "llama3.1:8b",
    },
    "openai": {
        "label": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "claude": {
        "label": "Claude (Anthropic)",
        "api_base": "https://api.anthropic.com/v1",
        "model": "claude-haiku-4-5",
    },
    "gemini": {
        "label": "Gemini (Google)",
        "api_base": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.0-flash",
    },
    "openai_compat": {
        "label": "Compatible (OpenAI API)",
        "api_base": "http://127.0.0.1:11434/v1",
        "model": "llama3.1:8b",
    },
}

ANTHROPIC_VERSION = "2023-06-01"


def openai_chat_url(api_base: str) -> str:
    return api_base.rstrip("/") + "/chat/completions"


def claude_url(api_base: str) -> str:
    return api_base.rstrip("/") + "/messages"


def gemini_url(api_base: str, model: str) -> str:
    base = api_base.rstrip("/")
    return f"{base}/models/{model}:generateContent"


def _non_system_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    return [m for m in messages if m.get("role") != "system"]


def build_claude_payload(
    model: str,
    system: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    cleaned = []
    for m in _non_system_messages(messages):
        role = m.get("role", "")
        if role not in ("user", "assistant"):
            continue
        cleaned.append({"role": role, "content": m.get("content", "")})
    return {
        "model": model,
        "system": system,
        "messages": cleaned,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def build_gemini_payload(
    system: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    contents: list[dict[str, Any]] = []
    for m in _non_system_messages(messages):
        role = m.get("role", "")
        if role == "user":
            grole = "user"
        elif role == "assistant":
            grole = "model"
        else:
            continue
        contents.append({"role": grole, "parts": [{"text": m.get("content", "")}]})
    return {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }


def extract_openai_text(data: dict[str, Any]) -> str:
    return data["choices"][0]["message"]["content"]


def extract_claude_text(data: dict[str, Any]) -> str:
    parts = data.get("content") or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text"]
    if not texts:
        texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
    return "".join(texts)


def extract_gemini_text(data: dict[str, Any]) -> str:
    cand = (data.get("candidates") or [None])[0] or {}
    parts = ((cand.get("content") or {}).get("parts")) or []
    return "".join(p.get("text", "") for p in parts if isinstance(p, dict))
