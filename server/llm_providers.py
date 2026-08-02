"""Defaults y mapeo de mensajes por proveedor LLM."""

from __future__ import annotations

from typing import Any

PROVIDERS = frozenset(
    {"ollama", "openai", "claude", "gemini", "openai_compat", "openrouter"}
)

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
    "openrouter": {
        "label": "OpenRouter",
        "api_base": "https://openrouter.ai/api/v1",
        "model": "openrouter/auto",
    },
}

ANTHROPIC_VERSION = "2023-06-01"
OPENROUTER_REFERER = "https://github.com/kapi21/SINTAXIA"
OPENROUTER_TITLE = "SINTAXIA"
OPENAI_COMPAT_PROVIDERS = frozenset({"openai", "openai_compat", "openrouter"})


def openai_chat_url(api_base: str) -> str:
    return api_base.rstrip("/") + "/chat/completions"


def openai_compat_headers(api_key: str = "", provider: str = "") -> dict[str, str]:
    """Headers Bearer (+ atribucion OpenRouter si aplica)."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if provider == "openrouter":
        headers["HTTP-Referer"] = OPENROUTER_REFERER
        headers["X-OpenRouter-Title"] = OPENROUTER_TITLE
    return headers


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
    """Extrae texto de chat completions OpenAI/OpenRouter.

    OpenRouter tipa content como string | null; a veces viene lista de parts.
    """
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"Respuesta LLM sin choices: {str(data)[:300]}")
    choice0 = choices[0] if isinstance(choices[0], dict) else {}
    err = choice0.get("error")
    if err:
        raise RuntimeError(f"Error del proveedor LLM: {err}")
    msg = choice0.get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if text:
                    parts.append(str(text))
        content = "".join(parts)
    if content is None or (isinstance(content, str) and not content.strip()):
        raise RuntimeError(
            "Respuesta LLM sin texto (content vacio/null). "
            f"finish={choice0.get('finish_reason')!r} model={data.get('model')!r}"
        )
    return str(content)


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
