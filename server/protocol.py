"""Paquete de respuesta CPC: T: / S: / E:."""

from __future__ import annotations

from typing import TypedDict

from cpc_text import normalize_cpc, wrap_lines

# MODE 1 = 40 cols. CPC string/LINE INPUT max ~255.
# "T:" + cuerpo debe quedar < 255 para no cortar en el Amstrad.
CPC_WIDTH = 40
CPC_MAX_LINES = 6
CPC_T_BODY_MAX = 250


class Packet(TypedDict):
    lines: list[str]
    sound: int
    error: int


def build_packet(lines: list[str], sound: int, error: int = 0) -> str:
    """Construye el cuerpo text/plain para el Amstrad."""
    sound = max(0, min(5, int(sound)))
    error = 1 if int(error) else 0
    safe_lines: list[str] = []
    truncated = False

    for idx, line in enumerate(lines):
        line = normalize_cpc(str(line))
        if not line:
            continue
        room = CPC_MAX_LINES - len(safe_lines)
        if room <= 0:
            truncated = True
            break
        if len(line) > CPC_WIDTH:
            full = wrap_lines(line, width=CPC_WIDTH, max_lines=99)
            chunk = full[:room]
            if len(full) > len(chunk):
                truncated = True
            safe_lines.extend(chunk)
        else:
            safe_lines.append(line[:CPC_WIDTH])
        if len(safe_lines) >= CPC_MAX_LINES:
            # Truncado solo si quedaba mas texto de entrada
            rest = [normalize_cpc(str(x)) for x in lines[idx + 1 :] if normalize_cpc(str(x))]
            if rest:
                truncated = True
            break

    if not safe_lines:
        safe_lines = ["..."]

    while True:
        t_body = "|".join(safe_lines)
        if len(t_body) <= CPC_T_BODY_MAX:
            break
        truncated = True
        if len(safe_lines) <= 1:
            t_body = safe_lines[0][: CPC_T_BODY_MAX - 3] + "..."
            safe_lines = [t_body]
            break
        safe_lines.pop()

    t_body = "|".join(safe_lines)
    if truncated and safe_lines:
        last = safe_lines[-1]
        if not last.endswith("..."):
            if len(last) > 37:
                safe_lines[-1] = last[:37] + "..."
            else:
                safe_lines[-1] = last + "..."
            t_body = "|".join(safe_lines)
            if len(t_body) > CPC_T_BODY_MAX:
                t_body = t_body[: CPC_T_BODY_MAX - 3] + "..."

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
    return build_packet(
        wrap_lines(text, width=CPC_WIDTH, max_lines=CPC_MAX_LINES),
        sound=sound,
        error=error,
    )
