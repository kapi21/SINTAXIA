"""Persistencia local de ajustes del servidor (settings.json)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from llm_providers import PROVIDERS

_DEFAULT_SETTINGS = Path(__file__).resolve().parent / "settings.json"


def settings_path() -> Path:
    """Ruta efectiva: env SINTAXIA_SETTINGS o server/settings.json."""
    env = (os.environ.get("SINTAXIA_SETTINGS") or "").strip()
    if env:
        return Path(env)
    return _DEFAULT_SETTINGS


SETTINGS_PATH = _DEFAULT_SETTINGS

_SETTINGS_KEYS = (
    "provider",
    "model",
    "ollama_url",
    "api_base",
    "api_key",
    "temperature",
    "mock",
    "system",
    "start_state",
    "setup_complete",
    "preferred_port",
)

PROVIDERS_NEEDING_KEY = frozenset({"openai", "claude", "gemini", "openrouter"})


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Lee settings.json. Devuelve {} si no existe o esta corrupto."""
    p = path if path is not None else settings_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"SETTINGS load error: {exc}")
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: data[k] for k in _SETTINGS_KEYS if k in data}


def is_setup_complete(data: dict[str, Any] | None) -> bool:
    """True si el asistente ya se completo (o settings legado usable)."""
    if not data:
        return False
    if "setup_complete" in data:
        return bool(data.get("setup_complete"))
    provider = str(data.get("provider") or "")
    model = str(data.get("model") or "").strip()
    if data.get("mock") is True:
        return True
    if provider in PROVIDERS and model:
        return True
    return False


def save_settings(
    ai: Any,
    *,
    mock: bool = False,
    setup_complete: bool | None = None,
    preferred_port: int | None = None,
    path: Path | None = None,
) -> None:
    """Escribe ajustes actuales a disco (incluye api_key)."""
    p = path if path is not None else settings_path()
    existing = load_settings(p) if p.is_file() else {}

    if setup_complete is None:
        setup_flag = bool(existing.get("setup_complete")) if "setup_complete" in existing else is_setup_complete(
            {
                "provider": getattr(ai, "provider", "ollama"),
                "model": getattr(ai, "model", ""),
                "mock": mock,
                **existing,
            }
        )
    else:
        setup_flag = bool(setup_complete)

    if preferred_port is None:
        port_val = existing.get("preferred_port")
    else:
        port_val = preferred_port

    payload: dict[str, Any] = {
        "provider": getattr(ai, "provider", "ollama"),
        "model": getattr(ai, "model", ""),
        "ollama_url": getattr(ai, "ollama_url", ""),
        "api_base": getattr(ai, "api_base", ""),
        "api_key": getattr(ai, "api_key", "") or "",
        "temperature": getattr(ai, "temperature", 0.7),
        "mock": bool(mock),
        "system": getattr(ai, "system", "") or "",
        "start_state": getattr(ai, "start_state", {}) or {},
        "setup_complete": setup_flag,
    }
    if port_val is not None:
        try:
            payload["preferred_port"] = int(port_val)
        except (TypeError, ValueError):
            pass

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"SETTINGS saved provider={payload['provider']} "
            f"model={payload['model']} setup={payload['setup_complete']} "
            f"key={'*' if payload['api_key'] else '(none)'}"
        )
    except OSError as exc:
        print(f"SETTINGS save error: {exc}")


def write_setup_stub(
    *,
    path: Path | None = None,
    preferred_port: int | None = None,
) -> None:
    """Tras reset: settings minimo con setup_complete false."""
    p = path if path is not None else settings_path()
    payload: dict[str, Any] = {"setup_complete": False, "mock": False}
    if preferred_port is not None:
        payload["preferred_port"] = int(preferred_port)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
