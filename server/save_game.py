"""Persistencia de partidas SINTAXIA (slots 1-3 en JSON)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_adventure import AdventureAI

SAVES_DIR = Path(__file__).resolve().parent / "saves"
MAX_SLOTS = 3


def ensure_saves_dir(base: Path | None = None) -> Path:
    d = base if base is not None else SAVES_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def slot_path(slot: int, base: Path | None = None) -> Path:
    slot = validate_slot(slot)
    d = ensure_saves_dir(base)
    return d / f"slot{slot}.json"


def validate_slot(slot: int | str) -> int:
    try:
        n = int(slot)
    except (TypeError, ValueError) as exc:
        raise ValueError("slot invalido") from exc
    if n < 1 or n > MAX_SLOTS:
        raise ValueError("slot debe ser 1..3")
    return n


def list_slots(base: Path | None = None) -> list[dict[str, Any]]:
    ensure_saves_dir(base)
    out: list[dict[str, Any]] = []
    for n in range(1, MAX_SLOTS + 1):
        path = slot_path(n, base)
        if not path.is_file():
            out.append({"slot": n, "occupied": False, "name": f"slot{n}", "saved_at": "", "summary": ""})
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            out.append({"slot": n, "occupied": False, "name": f"slot{n}", "saved_at": "", "summary": "corrupto"})
            continue
        state = data.get("state") if isinstance(data.get("state"), dict) else {}
        inv = state.get("inventory") if isinstance(state.get("inventory"), list) else []
        loc = state.get("location") or "?"
        inv_s = ", ".join(str(x) for x in inv[:4]) if inv else "(vacio)"
        out.append(
            {
                "slot": n,
                "occupied": True,
                "name": str(data.get("name") or f"slot{n}")[:32],
                "saved_at": str(data.get("saved_at") or ""),
                "summary": f"{loc} | {inv_s}",
                "location": loc,
                "inventory": list(inv),
            }
        )
    return out


def save_slot(ai: AdventureAI, slot: int, name: str | None = None, base: Path | None = None) -> dict[str, Any]:
    slot = validate_slot(slot)
    ensure_saves_dir(base)
    payload = ai.export_save()
    payload["slot"] = slot
    label = (name or "").strip() or f"slot{slot}"
    payload["name"] = label[:32]
    payload["saved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = slot_path(slot, base)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return payload


def load_slot(ai: AdventureAI, slot: int, base: Path | None = None) -> dict[str, Any]:
    slot = validate_slot(slot)
    path = slot_path(slot, base)
    if not path.is_file():
        raise FileNotFoundError(f"slot {slot} vacio")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("save corrupto")
    ai.import_save(data)
    return data


def delete_slot(slot: int, base: Path | None = None) -> bool:
    slot = validate_slot(slot)
    path = slot_path(slot, base)
    if path.is_file():
        path.unlink()
        return True
    return False

