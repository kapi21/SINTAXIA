"""Estado de partida SINTAXIA (inventario + flags + lugar)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class GameState:
    location: str = "entrada del castillo"
    inventory: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)

    def reset(self) -> None:
        self.location = "entrada del castillo"
        self.inventory.clear()
        self.flags.clear()

    def summary_for_prompt(self) -> str:
        inv = ", ".join(self.inventory) if self.inventory else "(vacio)"
        flags = ", ".join(f"{k}={'si' if v else 'no'}" for k, v in sorted(self.flags.items()))
        if not flags:
            flags = "(ninguno)"
        return (
            f"ESTADO PARTIDA:\n"
            f"- Lugar: {self.location}\n"
            f"- Inventario: {inv}\n"
            f"- Flags: {flags}\n"
            "Actualiza el estado si el jugador coge/deja objetos o cambia de sitio "
            "usando lineas I: y L: y F: en tu respuesta (ver reglas)."
        )

    def to_dict(self) -> dict:
        return {
            "location": self.location,
            "inventory": list(self.inventory),
            "flags": dict(self.flags),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> GameState:
        g = cls()
        if not isinstance(data, dict):
            return g
        loc = data.get("location")
        if isinstance(loc, str) and loc.strip():
            cleaned = re.sub(r"[^a-zA-Z0-9 _\-]", "", loc).strip().lower()
            cleaned = re.sub(r"\s+", " ", cleaned)[:48]
            if cleaned:
                g.location = cleaned
        inv = data.get("inventory")
        if isinstance(inv, list):
            g.inventory = [_norm_item(str(x)) for x in inv if _norm_item(str(x))]
        flags = data.get("flags")
        if isinstance(flags, dict):
            out: dict[str, bool] = {}
            for k, v in flags.items():
                key = re.sub(r"[^a-zA-Z0-9_]", "", str(k).lower())[:32]
                if not key:
                    continue
                if isinstance(v, bool):
                    out[key] = v
                elif isinstance(v, (int, float)):
                    out[key] = bool(v)
                elif isinstance(v, str):
                    out[key] = v.lower() in ("1", "si", "true", "yes")
            g.flags = out
        return g

    def apply_meta_lines(self, raw: str) -> str:
        """Aplica I:/L:/F: del LLM y devuelve el texto sin esas lineas."""
        if raw is None:
            raw = ""
        keep: list[str] = []
        for line in str(raw).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            s = line.strip()
            if not s:
                keep.append(line)
                continue
            low = s[:2].upper()
            if low == "I:" or s.upper().startswith("I:"):
                body = s[2:].strip()
                if body.startswith("+"):
                    item = _norm_item(body[1:])
                    if item and item not in self.inventory:
                        self.inventory.append(item)
                elif body.startswith("-"):
                    item = _norm_item(body[1:])
                    self.inventory = [x for x in self.inventory if x != item]
                elif body:
                    # lista completa separada por comas
                    items = [_norm_item(x) for x in body.split(",")]
                    self.inventory = [x for x in items if x]
                continue
            if s.upper().startswith("L:"):
                loc = _norm_item(s[2:])
                if loc:
                    self.location = loc
                continue
            if s.upper().startswith("F:"):
                # F:puerta_abierta=1  o F:trampa=0
                body = s[2:].strip()
                m = re.match(r"([A-Za-z0-9_]+)\s*=\s*([01]|si|no|true|false)", body, re.I)
                if m:
                    key = m.group(1).lower()
                    val = m.group(2).lower() in ("1", "si", "true")
                    self.flags[key] = val
                continue
            keep.append(line)
        return "\n".join(keep)


def _norm_item(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9 _\-]", "", text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text[:24]
