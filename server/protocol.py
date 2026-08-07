"""Paquete de respuesta CPC: T: / S: / E:."""

from __future__ import annotations

from typing import TypedDict

from cpc_text import join_narrative_segments, normalize_cpc, wrap_lines

# MODE 1 = 40 cols. MODE 2 = 80 cols (via ?cols=80).
# CPC LINE INPUT max ~255 por fila.
# Varias filas T: permiten hasta CPC_MAX_LINES sin un solo T$ gigante.
CPC_WIDTH = 40
CPC_WIDTH_MODE2 = 80
CPC_MAX_LINES = 12
CPC_T_BODY_MAX = 250


class Packet(TypedDict):
    lines: list[str]
    sound: int
    error: int


def clamp_cols(cols: int | None) -> int:
    """Solo dos perfiles: 40 (MODE 1) u 80 (MODE 2)."""
    if cols is None:
        return CPC_WIDTH
    try:
        c = int(cols)
    except (TypeError, ValueError):
        return CPC_WIDTH
    return CPC_WIDTH_MODE2 if c >= 60 else CPC_WIDTH


def reflow_lines(
    lines: list[str],
    *,
    width: int | None = None,
    max_lines: int | None = None,
) -> list[str]:
    """Une segmentos no vacios y re-envuelve para llenar el ancho (sin huecos)."""
    w = clamp_cols(width)
    limit = CPC_MAX_LINES if max_lines is None else max(1, int(max_lines))
    parts = [normalize_cpc(str(x)).strip() for x in lines]
    parts = [p for p in parts if p]
    if not parts:
        return []
    joined = join_narrative_segments(parts)
    return [L for L in wrap_lines(joined, width=w, max_lines=limit) if L.strip()]


def _chunk_t_bodies(safe_lines: list[str]) -> list[str]:
    """Parte lineas en cuerpos T: que no superen CPC_T_BODY_MAX."""
    chunks: list[str] = []
    current: list[str] = []
    for line in safe_lines:
        trial = "|".join(current + [line]) if current else line
        if current and len(trial) > CPC_T_BODY_MAX:
            chunks.append("|".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("|".join(current))
    return chunks or ["..."]


def build_packet(
    lines: list[str],
    sound: int,
    error: int = 0,
    *,
    max_lines: int | None = None,
    ellipsis: bool = True,
    width: int | None = None,
    reflow: bool = True,
) -> str:
    """Construye el cuerpo text/plain para el Amstrad (una o varias filas T:).

    max_lines: tope de segmentos (default CPC_MAX_LINES=12).
    width: 40 (MODE1) u 80 (MODE2).
    reflow: si True, une y re-envuelve para llenar el ancho.
    ellipsis: si True y hay recorte, anade '...' al final.
    """
    sound = max(0, min(5, int(sound)))
    error = 1 if int(error) else 0
    limit = CPC_MAX_LINES if max_lines is None else max(1, int(max_lines))
    w = clamp_cols(width)
    truncated = False

    cleaned = [normalize_cpc(str(x)).strip() for x in lines]
    cleaned = [x for x in cleaned if x]

    if reflow and cleaned:
        # Une restaurando puntos si el LLM uso | como fin de frase
        joined = join_narrative_segments(cleaned)
        full = wrap_lines(joined, width=w, max_lines=limit + 50)
        safe_lines = full[:limit]
        if len(full) > limit:
            truncated = True
    else:
        safe_lines = []
        for idx, line in enumerate(cleaned):
            room = limit - len(safe_lines)
            if room <= 0:
                truncated = True
                break
            if len(line) > w:
                full = [
                    L for L in wrap_lines(line, width=w, max_lines=max(room, 99)) if L.strip()
                ]
                chunk = full[:room]
                if len(full) > len(chunk):
                    truncated = True
                safe_lines.extend(chunk)
            else:
                safe_lines.append(line[:w])
            if len(safe_lines) >= limit:
                if cleaned[idx + 1 :]:
                    truncated = True
                break

    safe_lines = [L for L in safe_lines if L.strip()]

    if not safe_lines:
        safe_lines = ["..."]

    if truncated and ellipsis and safe_lines:
        last = safe_lines[-1]
        if not last.endswith("..."):
            cut = max(1, w - 3)
            if len(last) > cut:
                safe_lines[-1] = last[:cut] + "..."
            else:
                safe_lines[-1] = last + "..."

    bodies = _chunk_t_bodies(safe_lines)
    # Seguridad: una linea suelta no debe romper LINE INPUT
    fixed: list[str] = []
    for body in bodies:
        if len(body) <= CPC_T_BODY_MAX:
            fixed.append(body)
        else:
            fixed.append(body[: CPC_T_BODY_MAX - 3] + "...")
    out = "".join(f"T:{body}\r\n" for body in fixed)
    return f"{out}S:{sound}\r\nE:{error}\r\n"


def parse_packet(raw: str, max_lines: int | None = None) -> Packet:
    """Parsea un paquete; tolera CRLF, varias filas T: y lineas extra."""
    limit = CPC_MAX_LINES if max_lines is None else max(1, int(max_lines))
    lines: list[str] = []
    sound = 0
    error = 0
    for part in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("T:") or part.startswith("t:"):
            body = part[2:]
            lines.extend(
                x
                for x in (normalize_cpc(seg).strip() for seg in body.split("|"))
                if x
            )
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
    return {"lines": lines[:limit], "sound": sound, "error": error}


def packet_from_text(
    text: str,
    sound: int = 0,
    error: int = 0,
    *,
    width: int | None = None,
    max_lines: int | None = None,
) -> str:
    """Atajo: texto libre -> wrap denso + paquete."""
    w = clamp_cols(width)
    limit = CPC_MAX_LINES if max_lines is None else max(1, int(max_lines))
    return build_packet(
        wrap_lines(text, width=w, max_lines=limit),
        sound=sound,
        error=error,
        width=w,
        max_lines=limit,
        reflow=True,
    )
