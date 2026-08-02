"""Paquete de respuesta CPC: T: / S: / E:."""

from __future__ import annotations

from typing import TypedDict

from cpc_text import normalize_cpc, wrap_lines


class Packet(TypedDict):
    lines: list[str]
    sound: int
    error: int


def build_packet(lines: list[str], sound: int, error: int = 0) -> str:
    """Construye el cuerpo text/plain para el Amstrad."""
    sound = max(0, min(5, int(sound)))
    error = 1 if int(error) else 0
    safe_lines: list[str] = []
    for line in lines:
        line = normalize_cpc(str(line))
        if not line:
            continue
        # Garantizar <=40 por linea
        if len(line) > 40:
            safe_lines.extend(wrap_lines(line, width=40, max_lines=8 - len(safe_lines)))
        else:
            safe_lines.append(line)
        if len(safe_lines) >= 8:
            break
    if not safe_lines:
        safe_lines = ["..."]
    t_body = "|".join(safe_lines[:8])
    # CRLF: LINE INPUT del CPC corta en CR, no en LF solo
    return f"T:{t_body}\r\nS:{sound}\r\nE:{error}\r\n"


def parse_packet(raw: str) -> Packet:
    """Parsea un paquete; tolera CRLF y lineas extra."""
    lines: list[str] = []
    sound = 0
    error = 0
    for part in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("T:") or part.startswith("t:"):
            body = part[2:]
            lines = [normalize_cpc(x) for x in body.split("|") if normalize_cpc(x)]
        elif part.startswith("S:") or part.startswith("s:"):
            try:
                sound = max(0, min(5, int(part[2:].strip())))
            except ValueError:
                sound = 0
        elif part.startswith("E:") or part.startswith("e:"):
            try:
                error = 1 if int(part[2:].strip()) else 0
            except ValueError:
                error = 1
    if not lines:
        lines = ["Sin texto"]
        error = 1
    return {"lines": lines, "sound": sound, "error": error}


def packet_from_text(text: str, sound: int = 0, error: int = 0) -> str:
    """Atajo: texto libre -> wrap + paquete."""
    return build_packet(wrap_lines(text), sound=sound, error=error)
