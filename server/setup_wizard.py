"""Logica del asistente de configuracion (setup wizard)."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any

from llm_providers import DEFAULTS as PROV_DEFAULTS
from llm_providers import PROVIDERS
from save_game import MAX_SLOTS, delete_slot
from settings_store import (
    PROVIDERS_NEEDING_KEY,
    is_setup_complete,
    load_settings,
    settings_path,
    write_setup_stub,
)

SETUP_RESET_PHRASE = "RECONFIGURAR"
SETUP_BLOCK_MSG = "Configura el servidor en el PC (/ui)."


def list_local_ips() -> list[str]:
    """IPs IPv4 locales utiles (LAN primero, luego 127.0.0.1)."""
    found: list[str] = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan = s.getsockname()[0]
        s.close()
        if lan and not lan.startswith("127."):
            found.append(lan)
    except OSError:
        pass
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and ip not in found and not ip.startswith("127."):
                found.append(ip)
    except OSError:
        pass
    if "127.0.0.1" not in found:
        found.append("127.0.0.1")
    return found


def build_status(
    *,
    listen_port: int,
    saved: dict[str, Any] | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    data = saved if saved is not None else load_settings(path)
    pref = data.get("preferred_port")
    try:
        preferred = int(pref) if pref is not None else None
    except (TypeError, ValueError):
        preferred = None
    return {
        "ok": True,
        "setup_complete": is_setup_complete(data),
        "preferred_port": preferred,
        "listen_port": int(listen_port),
        "local_ips": list_local_ips(),
        "providers": sorted(PROVIDERS),
        "defaults": {k: dict(v) for k, v in PROV_DEFAULTS.items()},
    }


def parse_preferred_port(raw: Any) -> int:
    try:
        port = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("preferred_port invalido") from exc
    if port < 1 or port > 65535:
        raise ValueError("preferred_port fuera de rango (1-65535)")
    return port


def validate_complete_body(body: dict[str, Any]) -> dict[str, Any]:
    """Valida el body de /api/setup/complete. Devuelve dict normalizado o raises ValueError."""
    if not isinstance(body, dict):
        raise ValueError("body invalido")

    mock = bool(body.get("mock"))
    provider = str(body.get("provider") or "ollama").strip()
    if provider not in PROVIDERS:
        raise ValueError("proveedor desconocido")

    model = str(body.get("model") or "").strip()
    api_key = body.get("api_key")
    key_str = "" if api_key is None else str(api_key).strip()

    if not mock:
        if not model:
            preset = PROV_DEFAULTS.get(provider) or {}
            model = str(preset.get("model") or "").strip()
        if not model:
            raise ValueError("modelo obligatorio en modo IA")
        if provider in PROVIDERS_NEEDING_KEY and not key_str and not body.get("api_key_on_server"):
            # api_key_on_server: el caller indica que ya hay key en el AI
            if not body.get("_has_server_key"):
                raise ValueError("api_key obligatoria para este proveedor")

    preferred_port = parse_preferred_port(body.get("preferred_port", 8080))

    out: dict[str, Any] = {
        "mock": mock,
        "provider": provider,
        "model": model or str((PROV_DEFAULTS.get(provider) or {}).get("model") or "llama3.1:8b"),
        "preferred_port": preferred_port,
    }
    for key in ("ollama_url", "api_base", "temperature", "system"):
        if key in body:
            out[key] = body[key]
    if key_str:
        out["api_key"] = key_str
    if isinstance(body.get("start_state"), dict):
        out["start_state"] = body["start_state"]
    return out


def wipe_all_slots(base: Path | None = None) -> int:
    """Borra slots 1..MAX_SLOTS. Devuelve cuantos ficheros se eliminaron."""
    n = 0
    for slot in range(1, MAX_SLOTS + 1):
        if delete_slot(slot, base=base):
            n += 1
    return n


def perform_settings_reset(
    *,
    confirm: str,
    path: Path | None = None,
    saves_base: Path | None = None,
    keep_preferred_port: int | None = None,
) -> dict[str, Any]:
    """Valida frase y deja settings en stub + borra saves."""
    if str(confirm or "") != SETUP_RESET_PHRASE:
        raise ValueError(f'confirm debe ser "{SETUP_RESET_PHRASE}"')
    deleted = wipe_all_slots(saves_base)
    write_setup_stub(path=path or settings_path(), preferred_port=keep_preferred_port)
    return {
        "ok": True,
        "setup_complete": False,
        "slots_deleted": deleted,
    }
