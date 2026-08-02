"""Persistencia local de ajustes del servidor (settings.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"

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
)


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Lee settings.json. Devuelve {} si no existe o esta corrupto."""
    p = path or SETTINGS_PATH
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


def save_settings(
    ai: Any,
    *,
    mock: bool = False,
    path: Path | None = None,
) -> None:
    """Escribe ajustes actuales a disco (incluye api_key)."""
    p = path or SETTINGS_PATH
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
    }
    try:
        p.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"SETTINGS saved provider={payload['provider']} "
            f"model={payload['model']} key={'*' if payload['api_key'] else '(none)'}"
        )
    except OSError as exc:
        print(f"SETTINGS save error: {exc}")
