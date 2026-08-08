"""Cliente LLM (Ollama, OpenAI, Claude, Gemini, OpenRouter, OpenAI-compatible) + empaquetado CPC."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from cpc_text import join_narrative_segments, normalize_cpc, wrap_lines
from game_state import GameState
from llm_providers import (
    ANTHROPIC_VERSION,
    DEFAULTS,
    OPENAI_COMPAT_PROVIDERS,
    PROVIDERS,
    build_claude_payload,
    build_gemini_payload,
    claude_url,
    extract_claude_text,
    extract_gemini_text,
    extract_openai_text,
    gemini_url,
    openai_chat_url,
    openai_compat_headers,
)
from protocol import (
    CPC_MAX_LINES,
    CPC_WIDTH,
    build_packet,
    clamp_cols,
    packet_from_text,
    parse_packet,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
DEFAULT_OPENAI_BASE = "http://127.0.0.1:11434/v1"

_SOUND_KEYWORDS: list[tuple[tuple[str, ...], int]] = [
    (("peligro", "trampa", "monstruo", "dragon", "oscur", "miedo", "sangre"), 1),
    (("cueva", "caverna", "eco", "humedad", "sotano", "cripta"), 2),
    (("espada", "llave", "cofre", "amuleto", "pocion", "objeto", "encuentras", "hallas"), 3),
    (("golpe", "lucha", "ataque", "combate", "herid", "enemigo", "choque"), 4),
    (("tesoro", "victoria", "ganas", "escapas", "salvado", "luz llena"), 5),
]


def load_system_prompt() -> str:
    path = ROOT / "prompts" / "master.txt"
    return path.read_text(encoding="utf-8")


def load_fixed_rules() -> str:
    path = ROOT / "prompts" / "rules_fixed.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    # Fallback minimo si falta el fichero
    return (
        "REGLAS ESTRICTAS DE SALIDA:\n"
        "T:texto|en|segmentos\nS:N\nE:0\n"
        "Cada etiqueta en su linea. Max chars por segmento T: segun ANCHO. ASCII."
    )


_PROMPT_GEN_SYSTEM = (
    "Eres un disenador de mundos para aventuras de texto (Amstrad CPC). "
    "Respondes SOLO con el formato pedido en ASCII sin tildes ni enes, "
    "sin markdown y sin explicaciones."
)

_PROMPT_GEN_USER = """Inventa un MUNDO NUEVO para una aventura conversacional (NO un castillo medieval clasico).

NO escribas las reglas tecnicas T/S/E del juego: eso lo anade el servidor.
Tu SOLO defines el mundo creativo y el estado inicial.

Devuelve EXACTAMENTE:

===WORLD===
TITLE: nombre corto del escenario
PREMISE: 2 a 4 frases con el trasfondo (quien es el jugador, que pasa)
TONE: 3-6 palabras (ej. tension fria, misterio industrial)
HOOK: una frase de gancho al empezar
EXAMPLE_T: tres o cuatro segmentos unidos por | (max 40 chars cada uno, ASCII) como ejemplo de narracion de este mundo
EXAMPLE_S: un numero 0-5 acorde al tono

===STATE===
L:lugar_inicial_corto
I:objeto1, objeto2
F:clave1=0
F:clave2=1

Notas STATE:
- L: debe ser el sitio donde empieza el jugador (coherente con PREMISE)
- I: 0 a 3 objetos iniciales (o linea I: vacia)
- F: 1 a 4 flags snake_case con =0 o =1
- Todo ASCII sin tildes

No escribas nada fuera de ===WORLD=== y ===STATE===."""


DEFAULT_START_STATE: dict[str, Any] = {
    "location": "entrada del castillo",
    "inventory": [],
    "flags": {},
}


def _strip_fences(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text.strip()


def _parse_state_block(block: str) -> dict[str, Any]:
    """Parsea L:/I:/F: de un bloque STATE a dict GameState."""
    loc = ""
    inventory: list[str] = []
    flags: dict[str, bool] = {}
    for line in block.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if not s:
            continue
        up = s.upper()
        if up.startswith("L:"):
            loc = s[2:].strip()
        elif up.startswith("I:"):
            body = s[2:].strip()
            if body:
                inventory = [x.strip() for x in body.split(",") if x.strip()]
        elif up.startswith("F:"):
            body = s[2:].strip()
            m = re.match(r"([A-Za-z0-9_]+)\s*=\s*([01]|si|no|true|false)", body, re.I)
            if m:
                flags[m.group(1).lower()] = m.group(2).lower() in ("1", "si", "true")
    data = {
        "location": loc or DEFAULT_START_STATE["location"],
        "inventory": inventory,
        "flags": flags,
    }
    return GameState.from_dict(data).to_dict()


def _parse_world_fields(block: str) -> dict[str, str]:
    fields = {
        "title": "",
        "premise": "",
        "tone": "",
        "hook": "",
        "example_t": "",
        "example_s": "2",
    }
    for line in block.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if not s or ":" not in s:
            continue
        key, val = s.split(":", 1)
        key = key.strip().upper()
        val = val.strip()
        if key == "TITLE":
            fields["title"] = val
        elif key == "PREMISE":
            fields["premise"] = val
        elif key == "TONE":
            fields["tone"] = val
        elif key == "HOOK":
            fields["hook"] = val
        elif key == "EXAMPLE_T":
            fields["example_t"] = val
        elif key == "EXAMPLE_S":
            digits = re.sub(r"\D", "", val)
            if digits:
                fields["example_s"] = str(max(0, min(5, int(digits[0]))))
    return fields


def assemble_system_prompt(world: dict[str, str], state: dict[str, Any]) -> str:
    """Monta system prompt compatible: mundo generado + reglas fijas del servidor."""
    rules = load_fixed_rules()
    title = normalize_cpc(world.get("title") or "Aventura desconocida")
    premise = normalize_cpc(world.get("premise") or "Despiertas en un lugar extrano.")
    tone = normalize_cpc(world.get("tone") or "misterio")
    hook = normalize_cpc(world.get("hook") or "Algo te espera.")
    loc = normalize_cpc(str(state.get("location") or "lugar desconocido"))
    example_t = world.get("example_t") or (
        f"Estas en {loc}.|El aire es denso.|Que haces?"
    )
    example_t = normalize_cpc(example_t.replace("\n", "|"))
    # Asegurar segmentos cortos
    segs = [s.strip()[:40] for s in example_t.split("|") if s.strip()][:6]
    if not segs:
        segs = [f"Estas en {loc}."[:40], "Que haces?"]
    example_t = "|".join(segs)
    example_s = world.get("example_s") or "2"

    inv = state.get("inventory") or []
    inv_line = ", ".join(str(x) for x in inv) if inv else "(vacio)"
    flags = state.get("flags") or {}

    out = (
        "Eres el Master de una aventura de texto clasica para Amstrad CPC (1984).\n"
        "\n"
        "MUNDO DE ESTA PARTIDA:\n"
        f"- Titulo/tema: {title}\n"
        f"- Premisa: {premise}\n"
        f"- Tono: {tone}\n"
        f"- El jugador empieza en: {loc}\n"
        f"- Inventario inicial: {inv_line}\n"
        f"- Gancho: {hook}\n"
        "\n"
        "REGLAS DE NARRATIVA Y COHERENCIA:\n"
        "- Manten continuidad logica con el entorno, el historial y este mundo.\n"
        "- Permanece en el lugar actual (L:) hasta que el jugador se mueva de forma explicita.\n"
        "- Consecuencias directas y verosimiles; sin giros absurdos ni cambios de escenario sorpresa.\n"
        "- No inventes objetos que contradigan el inventario salvo que el jugador los encuentre.\n"
        "- Escribe con coherencia: mayusculas, puntuacion y gramatica correctas (ASCII sin tildes).\n"
        "\n"
        f"{rules}\n"
        "\n"
        "Ejemplo valido para ESTE mundo:\n"
        f"T:{example_t}\n"
        f"S:{example_s}\n"
        "E:0\n"
        f"L:{loc}\n"
    )
    if flags:
        for k, v in sorted(flags.items()):
            out += f"F:{k}={'1' if v else '0'}\n"
    return out.strip()


_MUNDO_FIELD_PATTERNS: tuple[tuple[str, str], ...] = (
    ("title", r"(?im)^\s*-\s*Titulo/tema:\s*(.+)$"),
    ("premise", r"(?im)^\s*-\s*Premisa:\s*(.+)$"),
    ("tone", r"(?im)^\s*-\s*Tono:\s*(.+)$"),
    ("location", r"(?im)^\s*-\s*El jugador empieza en:\s*(.+)$"),
    ("inventory", r"(?im)^\s*-\s*Inventario inicial:\s*(.+)$"),
    ("hook", r"(?im)^\s*-\s*Gancho:\s*(.+)$"),
)


def parse_mundo_fields(system: str) -> dict[str, str]:
    """Extrae campos del bloque MUNDO DE ESTA PARTIDA del system prompt."""
    text = system or ""
    m = re.search(
        r"MUNDO DE ESTA PARTIDA:\s*(.*?)(?=\n\s*REGLAS|\n\s*===|\Z)",
        text,
        flags=re.I | re.S,
    )
    block = m.group(1) if m else text
    out: dict[str, str] = {}
    for key, pat in _MUNDO_FIELD_PATTERNS:
        fm = re.search(pat, block)
        if fm:
            out[key] = normalize_cpc(fm.group(1).strip())
    return out


def scrub_history_snippet(text: str, max_len: int = 120) -> str:
    """Texto de historial limpio para recap de LOAD (ASCII, sin T:/S:)."""
    t = normalize_cpc(str(text or ""))
    t = re.sub(r"(?i)^T:", "", t).strip()
    t = re.sub(r"(?i)\b[SEILF]:\S*", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > max_len:
        t = t[: max_len - 3].rstrip() + "..."
    return t


# Historial enviado al LLM = mismo tope que se guarda (antes: guardaba 12 y solo enviaba 6).
MAX_HISTORY_MESSAGES = 20  # ~10 turnos (user+assistant)
MAX_PLOT_SUMMARY_CHARS = 1200
PLOT_COMPACT_THRESHOLD = 900

_PLOT_COMPACT_SYSTEM = (
    "Eres el archivero de una aventura de texto. "
    "Resume SOLO hechos permanentes ya ocurridos (lugares visitados, objetos, PNJs, "
    "puertas, promesas, peligros). ASCII sin tildes ni enes. "
    "Maximo 10 lineas cortas. Sin inventar. Sin formato T:/S:."
)


def fold_plot_summary(
    existing: str,
    dropped: list[dict[str, str]] | None,
    *,
    max_chars: int = MAX_PLOT_SUMMARY_CHARS,
) -> str:
    """Incorpora mensajes caidos del historial a la memoria de trama (local)."""
    bits: list[str] = []
    for item in dropped or []:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", ""))
        content = scrub_history_snippet(str(item.get("content", "")), 140)
        if not content:
            continue
        prefix = "J:" if role == "user" else "N:"
        bits.append(f"{prefix} {content}")
    chunk = " | ".join(bits).strip()
    base = normalize_cpc(str(existing or "").strip())
    if chunk:
        merged = f"{base} || {chunk}".strip(" |") if base else chunk
    else:
        merged = base
    merged = re.sub(r"\s+", " ", merged).strip()
    if len(merged) <= max_chars:
        return merged
    # Conservar el final (hechos mas recientes del resumen)
    return ("..." + merged[-(max_chars - 3) :]).strip()


def plot_summary_for_prompt(summary: str) -> str:
    s = normalize_cpc(str(summary or "").strip())
    if not s:
        return ""
    return (
        "MEMORIA DE TRAMA (hechos ya ocurridos; no los contradigas ni los borres):\n"
        f"{s}\n"
        "Si un hecho nuevo es importante, reflejalo tambien con flags F: cuando aplique.\n"
    )


def build_load_resume_lines(
    system: str,
    state: dict[str, Any] | None,
    history: list[dict[str, str]] | None,
    *,
    had_system: bool = True,
    slot: int | None = None,
    width: int | None = None,
) -> list[str]:
    """Lineas de reanudacion tras LOAD: mundo + situacion + lo hecho."""
    w = clamp_cols(width)
    st = state or {}
    fields = parse_mundo_fields(system)
    loc = normalize_cpc(str(st.get("location") or fields.get("location") or "lugar desconocido"))
    inv_list = st.get("inventory") if isinstance(st.get("inventory"), list) else []
    inv = ", ".join(str(x) for x in inv_list) if inv_list else "(vacio)"
    inv = normalize_cpc(inv)
    flags = st.get("flags") if isinstance(st.get("flags"), dict) else {}
    flag_on = [str(k) for k, v in flags.items() if v]
    flag_s = ", ".join(flag_on[:4]) if flag_on else ""

    head = "Partida cargada."
    if slot is not None:
        head = f"Cargado slot {int(slot)}."

    chunks: list[str] = [head, "Te reubicas en la aventura."]
    if fields.get("title"):
        chunks.append(f"Mundo: {fields['title']}")
    if fields.get("premise"):
        # Premisa completa pero el wrap/max_lines recortaran luego
        chunks.append(f"Premisa: {fields['premise']}")
    if fields.get("tone"):
        chunks.append(f"Tono: {fields['tone']}")
    chunks.append("-- Situacion --")
    chunks.append(f"Lugar: {loc}")
    chunks.append(f"Llevas: {inv}")
    if flag_s:
        chunks.append(f"Hechos: {flag_s}")

    # Recap desde historial
    hist = history or []
    last_user = ""
    last_asst = ""
    for item in reversed(hist):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", ""))
        content = scrub_history_snippet(str(item.get("content", "")), 140)
        if not content:
            continue
        if role == "assistant" and not last_asst:
            last_asst = content
        elif role == "user" and not last_user:
            last_user = content
        if last_user and last_asst:
            break
    if last_user or last_asst:
        chunks.append("-- Hasta ahora --")
        if last_user:
            chunks.append(f"Tu ultima accion: {last_user}")
        if last_asst:
            chunks.append(f"El maestro: {last_asst}")

    if not had_system:
        chunks.append("Mundo no embebido; sigue el prompt actual.")

    chunks.append("Continua cuando quieras.")

    lines: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        wrapped = [L for L in wrap_lines(chunk, width=w, max_lines=12) if L.strip()]
        lines.extend(wrapped)
        if len(lines) >= CPC_MAX_LINES:
            break
    return [L for L in lines[:CPC_MAX_LINES] if L.strip()] or [
        "Partida cargada.",
        f"Lugar: {loc}",
        f"Llevas: {inv}",
    ]


def build_load_resume_packet(
    system: str,
    state: dict[str, Any] | None,
    history: list[dict[str, str]] | None,
    *,
    had_system: bool = True,
    slot: int | None = None,
    width: int | None = None,
) -> str:
    w = clamp_cols(width)
    lines = build_load_resume_lines(
        system,
        state,
        history,
        had_system=had_system,
        slot=slot,
        width=w,
    )
    return build_packet(lines, sound=0, error=0, width=w, reflow=False, max_lines=CPC_MAX_LINES)


# Tope amplio solo para /intro (resumen MUNDO completo). Turnos siguen en 12.
CPC_INTRO_MAX_LINES = 60


def build_mundo_intro_lines(
    system: str,
    state: dict[str, Any] | None = None,
    *,
    width: int | None = None,
) -> list[str]:
    """Lineas T: del resumen inicial = bloque MUNDO completo (sin tope 12)."""
    w = clamp_cols(width)
    st = state or {}
    fields = parse_mundo_fields(system)
    loc = fields.get("location") or normalize_cpc(str(st.get("location") or "lugar desconocido"))
    inv = fields.get("inventory")
    if not inv:
        inv_list = st.get("inventory") or []
        inv = ", ".join(str(x) for x in inv_list) if inv_list else "(vacio)"
    inv = normalize_cpc(inv)

    chunks = [
        "MUNDO DE ESTA PARTIDA:",
        f"Titulo: {fields['title']}" if fields.get("title") else "",
        f"Premisa: {fields['premise']}" if fields.get("premise") else "",
        f"Tono: {fields['tone']}" if fields.get("tone") else "",
        f"Lugar: {loc}",
        f"Inventario: {inv}",
        f"Gancho: {fields['hook']}" if fields.get("hook") else "",
    ]
    lines: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        wrapped = [
            L for L in wrap_lines(chunk, width=w, max_lines=CPC_INTRO_MAX_LINES) if L.strip()
        ]
        lines.extend(wrapped)
        if len(lines) >= CPC_INTRO_MAX_LINES:
            break
    # Sin renglones vacios entre bloques
    return [L for L in lines[:CPC_INTRO_MAX_LINES] if L.strip()] or [
        "MUNDO DE ESTA PARTIDA:",
        f"Lugar: {loc}",
    ]


def build_mundo_intro_packet(
    system: str,
    state: dict[str, Any] | None = None,
    *,
    width: int | None = None,
) -> str:
    w = clamp_cols(width)
    lines = build_mundo_intro_lines(system, state, width=w)
    return build_packet(
        lines,
        sound=2,
        error=0,
        max_lines=max(len(lines), 1),
        ellipsis=False,
        width=w,
        reflow=False,
    )


def parse_generated_bundle(raw: str) -> dict[str, Any]:
    """Parsea WORLD+STATE del LLM y ensambla prompt compatible con el servidor."""
    text = _strip_fences(raw)
    # Compat: antiguos bloques ===PROMPT=== (se tratan como premise cruda)
    if "===WORLD===" not in text.upper() and "===PROMPT===" in text.upper():
        # Intentar recuperar STATE y usar el prompt viejo como premise
        norm = text
        for tag in ("===PROMPT===", "===STATE==="):
            norm = re.sub(rf"^\s*{re.escape(tag)}\s*$", tag, norm, flags=re.I | re.M)
        sp = re.split(r"^===STATE===\s*$", norm, maxsplit=1, flags=re.M)
        old_prompt = re.sub(r"^===PROMPT===\s*", "", sp[0], flags=re.I | re.M).strip()
        state_block = sp[1].strip() if len(sp) > 1 else ""
        state = _parse_state_block(state_block) if state_block else dict(DEFAULT_START_STATE)
        world = {
            "title": "Aventura generada",
            "premise": normalize_cpc(old_prompt)[:500],
            "tone": "misterio",
            "hook": "La aventura comienza.",
            "example_t": f"Estas en {state['location']}.|Que haces?",
            "example_s": "2",
        }
        return {"system": assemble_system_prompt(world, state), "state": state}

    norm = text
    for tag in ("===WORLD===", "===STATE==="):
        norm = re.sub(rf"^\s*{re.escape(tag)}\s*$", tag, norm, flags=re.I | re.M)

    world_block = ""
    state_block = ""
    parts = re.split(r"^===WORLD===\s*$", norm, maxsplit=1, flags=re.M)
    if len(parts) == 2:
        rest = parts[1]
        sp = re.split(r"^===STATE===\s*$", rest, maxsplit=1, flags=re.M)
        world_block = sp[0].strip()
        state_block = sp[1].strip() if len(sp) > 1 else ""
    else:
        sp = re.split(r"^===STATE===\s*$", norm, maxsplit=1, flags=re.M)
        world_block = sp[0].replace("===WORLD===", "").strip()
        state_block = sp[1].strip() if len(sp) > 1 else ""

    world = _parse_world_fields(world_block)
    if not world["premise"] and not world["title"]:
        raise RuntimeError(
            "El modelo no devolvio un mundo usable. Reintenta o cambia de modelo."
        )
    state = _parse_state_block(state_block) if state_block.strip() else dict(DEFAULT_START_STATE)
    if not world["example_t"]:
        world["example_t"] = f"Estas en {state['location']}.|Que haces?"
    system = assemble_system_prompt(world, state)
    return {"system": system, "state": state}


def infer_sound(text: str) -> int:
    low = text.lower()
    for keys, code in _SOUND_KEYWORDS:
        if any(k in low for k in keys):
            return code
    return 0


def _extract_packetish(raw: str) -> str:
    raw = normalize_protocol_separators(raw.strip())
    raw = re.sub(r"```.*?```", "", raw, flags=re.S)
    m = re.search(r"(T:.*?)(?:\n\s*\n|$)", raw, flags=re.I | re.S)
    if m:
        block = m.group(1).strip()
        rest = raw[m.end() : m.end() + 120]
        if not re.search(r"^S:", block, re.I | re.M):
            sm = re.search(r"^S:\s*(\d)", rest, re.I | re.M) or re.search(
                r"S:\s*(\d)", raw, re.I
            )
            if sm:
                block += f"\nS:{sm.group(1)}"
        if not re.search(r"^E:", block, re.I | re.M):
            em = re.search(r"^E:\s*(\d)", rest, re.I | re.M) or re.search(
                r"E:\s*(\d)", raw, re.I
            )
            if em:
                block += f"\nE:{em.group(1)}"
            else:
                block += "\nE:0"
        return block
    return raw


def normalize_protocol_separators(raw: str) -> str:
    """Convierte T:/S:2/E:0/I:... (mal formado) en lineas reales.

    Algunos modelos (y prompts generados) unen campos con '/' en vez de CRLF.
    """
    if not raw:
        return raw
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # "/S:" "/E:" "/I:" "/L:" "/F:" -> salto de linea + etiqueta
    text = re.sub(r"(?i)\s*/([TSEILF]):", r"\n\1:", text)
    # Tambien "|S:" etc. si el meta va tras un pipe (no es linea de T:)
    text = re.sub(r"(?i)\|([SEILF]):", r"\n\1:", text)
    return text


def scrub_narrative_leaks(text: str) -> str:
    """Quita S:/E:/I:/L:/F: colados dentro del texto narrativo."""
    if not text:
        return text
    # Corta desde el primer meta inline (/S: |S: o espacio+S:)
    m = re.search(r"(?i)(?:[/|]\s*|(?<=\s))([SEILF]):", text)
    if m:
        text = text[: m.start()].rstrip(" /|\t")
    # Pegado al final sin separador: "...norteS:2"
    text = re.sub(r"(?i)(?<![A-Za-z0-9])([SEILF]):\S*.*$", "", text).rstrip()
    return text.strip()


def repack_llm_text(raw: str, *, width: int | None = None) -> str:
    w = clamp_cols(width)
    candidate = _extract_packetish(raw)
    pkt = parse_packet(candidate)
    if pkt["lines"] == ["Sin texto"] or (
        pkt["error"] == 1 and pkt["lines"] and "Sin texto" in pkt["lines"][0]
    ):
        text = normalize_cpc(re.sub(r"^T:", "", raw, flags=re.I))
        text = scrub_narrative_leaks(text)
        text = re.sub(r"(?i)[SEILF]:\s*\S+", " ", text)
        lines = wrap_lines(text, width=w, max_lines=CPC_MAX_LINES)
        sound = infer_sound(text)
        return build_packet(
            lines or ["El maestro duda un momento."],
            sound=sound,
            error=0,
            width=w,
        )

    sound = pkt["sound"]
    cleaned_parts = [scrub_narrative_leaks(x).strip() for x in pkt["lines"]]
    cleaned_parts = [x for x in cleaned_parts if x]
    if sound == 0:
        sound = infer_sound(" ".join(cleaned_parts))
    joined = join_narrative_segments(cleaned_parts)
    joined = scrub_narrative_leaks(joined)
    lines = [L for L in wrap_lines(joined, width=w, max_lines=CPC_MAX_LINES) if L.strip()]
    if not lines:
        lines = [
            normalize_cpc(x)[:w]
            for x in cleaned_parts[:CPC_MAX_LINES]
            if normalize_cpc(x).strip()
        ]
    return build_packet(lines, sound=sound, error=0, width=w)


def list_ollama_models(tags_url: str = "http://127.0.0.1:11434/api/tags") -> list[str]:
    """Lista modelos disponibles en Ollama local."""
    try:
        with urllib.request.urlopen(tags_url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def list_provider_models(
    provider: str,
    api_base: str = "",
    api_key: str = "",
    ollama_url: str = DEFAULT_OLLAMA_CHAT,
) -> list[str]:
    """
    Devuelve la lista de modelos disponibles para el proveedor indicado.

    - ollama      → GET {api/tags}         (sin autenticación)
    - openai/compat/openrouter → GET {api_base}/models (Bearer api_key)
    - claude      → GET https://api.anthropic.com/v1/models (x-api-key)
    - gemini      → GET {api_base}/models?key=api_key
    """
    try:
        if provider == "ollama":
            # Derivamos la URL base de Ollama quitando el path de chat
            base = ollama_url.rstrip("/")
            for suffix in ("/api/chat", "/v1/chat/completions", "/v1"):
                if base.endswith(suffix):
                    base = base[: -len(suffix)]
                    break
            tags_url = base.rstrip("/") + "/api/tags"
            # Hacemos la petición directamente para que los errores (Ollama
            # apagado, URL incorrecta, timeout) propaguen al except exterior
            # y lleguen al panel como mensaje legible en lugar de lista vacía.
            with urllib.request.urlopen(tags_url, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            names = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return sorted(names)

        if provider in OPENAI_COMPAT_PROVIDERS:
            if not api_base:
                from llm_providers import DEFAULTS
                api_base = DEFAULTS.get(provider, {}).get("api_base", "https://api.openai.com/v1")
            url = api_base.rstrip("/") + "/models"
            headers = openai_compat_headers(api_key, provider)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
            return sorted(models)

        if provider == "claude":
            from llm_providers import ANTHROPIC_VERSION
            if not api_base:
                api_base = "https://api.anthropic.com/v1"
            url = api_base.rstrip("/") + "/models"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # Anthropic devuelve {"data": [...], ...}
            raw = data.get("data") or []
            models = [m.get("id", "") for m in raw if m.get("id")]
            return sorted(models)

        if provider == "gemini":
            if not api_base:
                api_base = "https://generativelanguage.googleapis.com/v1beta"
            url = api_base.rstrip("/") + "/models"
            if api_key:
                url += "?key=" + urllib.parse.quote(api_key, safe="")
            headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # Gemini devuelve {"models": [{"name": "models/gemini-2.0-flash", ...}]}
            raw = data.get("models") or []
            models = []
            for m in raw:
                name = m.get("name", "")
                if name.startswith("models/"):
                    name = name[len("models/"):]
                if name:
                    models.append(name)
            return sorted(models)

    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc

    return []



class AdventureAI:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        provider: str = "ollama",
        ollama_url: str = DEFAULT_OLLAMA_CHAT,
        api_base: str = DEFAULT_OPENAI_BASE,
        api_key: str = "",
        temperature: float = 0.7,
        system: str | None = None,
    ) -> None:
        self.model = model
        self.provider = provider if provider in PROVIDERS else "ollama"
        self.ollama_url = ollama_url
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.temperature = temperature
        self.system = system if system is not None else load_system_prompt()
        self.history: list[dict[str, str]] = []
        self.max_history = MAX_HISTORY_MESSAGES  # mensajes (user+assistant) guardados Y enviados
        self.plot_summary = ""
        self.state = GameState()
        self.start_state: dict[str, Any] = dict(DEFAULT_START_STATE)
        self.last_user = ""
        self.last_packet = ""
        self.last_error = ""
        self._intro_packet: str | None = None
        self._intro_key = ""

    def reset(self, *, width: int | None = None) -> str:
        """Reinicia historial y estado al mundo base actual del servidor."""
        w = clamp_cols(width)
        self.history.clear()
        self.plot_summary = ""
        self.state = GameState.from_dict(self.start_state)
        self.last_user = "(reset)"
        self.last_error = ""
        self._intro_packet = None
        self._intro_key = ""
        packet = packet_from_text(
            "Partida reiniciada.",
            sound=0,
            error=0,
            width=w,
        )
        self.last_packet = packet
        return packet

    def export_save(self) -> dict[str, Any]:
        hist = self.history[-self.max_history :]
        clean_hist: list[dict[str, str]] = []
        for item in hist:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", ""))
            content = str(item.get("content", ""))
            if role in ("user", "assistant") and content:
                clean_hist.append({"role": role, "content": content[:500]})
        start = GameState.from_dict(self.start_state).to_dict()
        return {
            "system": str(self.system or ""),
            "start_state": start,
            "state": self.state.to_dict(),
            "history": clean_hist,
            "plot_summary": str(self.plot_summary or "")[:MAX_PLOT_SUMMARY_CHARS],
        }

    def import_save(
        self,
        data: dict[str, Any],
        *,
        width: int | None = None,
        slot: int | None = None,
    ) -> None:
        if not isinstance(data, dict):
            data = {}
        had_system = False
        sys_raw = data.get("system")
        if isinstance(sys_raw, str) and sys_raw.strip():
            self.system = sys_raw
            self._intro_packet = None
            self._intro_key = ""
            had_system = True
        ss = data.get("start_state")
        if isinstance(ss, dict):
            self.start_state = GameState.from_dict(ss).to_dict()
        self.state = GameState.from_dict(data.get("state"))
        self.history = []
        hist = data.get("history")
        if isinstance(hist, list):
            for item in hist[-self.max_history :]:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role", ""))
                content = str(item.get("content", ""))
                if role in ("user", "assistant") and content:
                    self.history.append({"role": role, "content": content[:500]})
        ps = data.get("plot_summary")
        self.plot_summary = (
            normalize_cpc(str(ps))[:MAX_PLOT_SUMMARY_CHARS]
            if isinstance(ps, str) and ps.strip()
            else ""
        )
        self.last_error = ""
        self.last_user = "(load)"
        self.last_packet = build_load_resume_packet(
            self.system,
            self.state.to_dict(),
            self.history,
            had_system=had_system,
            slot=slot,
            width=width,
        )
    def config_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "ollama_url": self.ollama_url,
            "api_base": self.api_base,
            "openai_base": self.api_base,
            "api_key_set": bool(self.api_key),
            "temperature": self.temperature,
            "system": self.system,
            "start_state": dict(self.start_state) if isinstance(self.start_state, dict) else {},
            "history_len": len(self.history),
            "plot_summary": self.plot_summary,
            "last_user": self.last_user,
            "last_packet": self.last_packet,
            "last_error": self.last_error,
            "state": self.state.to_dict(),
        }

    def apply_config(self, data: dict[str, Any]) -> None:
        if "provider" in data and data["provider"] in PROVIDERS:
            self.provider = data["provider"]
        if "model" in data and str(data["model"]).strip():
            self.model = str(data["model"]).strip()
        if "ollama_url" in data and str(data["ollama_url"]).strip():
            self.ollama_url = str(data["ollama_url"]).strip()
        base_set = False
        for key in ("api_base", "openai_base"):
            if key not in data:
                continue
            raw = str(data[key]).strip()
            if raw:
                self.api_base = raw.rstrip("/")
                base_set = True
                break
            # Cadena vacia explicita (p. ej. Ollama): limpiar base
            self.api_base = ""
            base_set = True
            break
        if not base_set and "provider" in data and data["provider"] in PROVIDERS:
            preset_base = DEFAULTS.get(self.provider, {}).get("api_base") or ""
            self.api_base = str(preset_base).rstrip("/") if preset_base else ""
        if "api_key" in data:
            # cadena vacia = no tocar; " " especial? None clear
            key = data["api_key"]
            if key is None:
                pass
            elif key == "":
                pass
            else:
                self.api_key = str(key)
        if "temperature" in data:
            try:
                self.temperature = max(0.0, min(2.0, float(data["temperature"])))
            except (TypeError, ValueError):
                pass
        if "system" in data and isinstance(data["system"], str) and data["system"].strip():
            new_sys = data["system"]
            if new_sys != self.system:
                self._intro_packet = None
                self._intro_key = ""
            self.system = new_sys
        if "start_state" in data and isinstance(data["start_state"], dict):
            self.start_state = GameState.from_dict(data["start_state"]).to_dict()
            self.state = GameState.from_dict(self.start_state)
            self.history.clear()
            self.plot_summary = ""
            self._intro_packet = None
            self._intro_key = ""
            self.last_error = ""
            self.last_user = "(nuevo mundo)"
            inv = ", ".join(self.state.inventory) if self.state.inventory else "(vacio)"
            self.last_packet = packet_from_text(
                f"Nuevo mundo. Lugar: {self.state.location}. Llevas: {inv}.",
                sound=0,
                error=0,
            )
        elif data.get("reset_start_state"):
            self.start_state = dict(DEFAULT_START_STATE)
            self.state = GameState.from_dict(self.start_state)
            self.history.clear()
            self.plot_summary = ""
            self._intro_packet = None
            self._intro_key = ""
            self.last_user = "(mundo por defecto)"

    def _messages(self, user_msg: str, *, width: int | None = None) -> list[dict[str, str]]:
        w = clamp_cols(width)
        memory = plot_summary_for_prompt(self.plot_summary)
        system = (
            self.system
            + "\n\n"
            + self.state.summary_for_prompt()
            + (("\n\n" + memory) if memory else "")
            + f"\n\nANCHO PANTALLA CPC: cada segmento T: MAXIMO {w} caracteres. "
            f"Llena cada segmento cerca de {w} chars; sin segmentos vacios ni cortos a proposito."
            + "\n\nEscribe con coherencia: mayusculas al inicio de frase, "
            "puntuacion y gramatica correctas. ASCII sin tildes ni enes."
        )
        messages = [{"role": "system", "content": system}]
        messages.extend(self.history[-self.max_history :])
        messages.append({"role": "user", "content": user_msg})
        return messages

    def _trim_history(self) -> None:
        """Recorta historial al tope; lo caido pasa a plot_summary."""
        limit = int(self.max_history)
        if len(self.history) <= limit:
            return
        dropped = self.history[:-limit]
        self.history = self.history[-limit:]
        self.plot_summary = fold_plot_summary(self.plot_summary, dropped)
        # Compactar con LLM solo si el resumen se hincha (evita una 2a llamada cada turno).
        if len(self.plot_summary) >= PLOT_COMPACT_THRESHOLD:
            self._compact_plot_summary()

    def _compact_plot_summary(self, timeout: float = 45.0) -> None:
        """Reduce plot_summary con un one-shot LLM; si falla, deja el fold local."""
        raw = self.plot_summary.strip()
        if not raw:
            return
        user = (
            "Resume y fusiona esta memoria de trama. Conserva todos los hechos utiles:\n\n"
            + raw[:2000]
        )
        try:
            out = self._one_shot_chat(_PLOT_COMPACT_SYSTEM, user, timeout=timeout)
            cleaned = normalize_cpc(out)
            cleaned = re.sub(r"(?i)\b[TSEILF]:\S*", " ", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if cleaned:
                self.plot_summary = cleaned[:MAX_PLOT_SUMMARY_CHARS]
        except Exception as exc:
            print(f"PLOT compact skip: {exc}")

    def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:400]
            except Exception:
                detail = ""
            msg = f"HTTP {exc.code} {exc.reason}"
            if detail:
                msg += f": {detail}"
            raise RuntimeError(msg) from exc

    def _chat_ollama(self, user_msg: str, timeout: float = 120.0, *, width: int | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": self._messages(user_msg, width=width),
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 500,
            },
        }
        data = self._post_json(
            self.ollama_url,
            payload,
            {"Content-Type": "application/json"},
            timeout,
        )
        return data["message"]["content"]

    def _chat_openai_compat(self, user_msg: str, timeout: float = 120.0, *, width: int | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": self._messages(user_msg, width=width),
            "temperature": self.temperature,
            "max_tokens": 500,
        }
        headers = openai_compat_headers(self.api_key, self.provider)
        data = self._post_json(
            openai_chat_url(self.api_base), payload, headers, timeout
        )
        return extract_openai_text(data)

    def _chat_claude(self, user_msg: str, timeout: float = 120.0, *, width: int | None = None) -> str:
        messages = self._messages(user_msg, width=width)
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else self.system
        payload = build_claude_payload(
            self.model, system, messages, self.temperature, 500
        )
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        }
        data = self._post_json(claude_url(self.api_base), payload, headers, timeout)
        return extract_claude_text(data)

    def _chat_gemini(self, user_msg: str, timeout: float = 120.0, *, width: int | None = None) -> str:
        if not self.api_key.strip():
            raise RuntimeError("Falta API key de Gemini. Pegala en el panel y pulsa Guardar.")
        messages = self._messages(user_msg, width=width)
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else self.system
        payload = build_gemini_payload(system, messages, self.temperature, 500)
        url = gemini_url(self.api_base, self.model)
        # Google acepta ?key= (mas compatible) y header x-goog-api-key
        url = f"{url}?key={urllib.parse.quote(self.api_key, safe='')}"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        data = self._post_json(url, payload, headers, timeout)
        text = extract_gemini_text(data)
        if not text.strip():
            raise RuntimeError(f"Gemini respondio vacio: {json.dumps(data)[:300]}")
        return text

    def _chat(self, user_msg: str, timeout: float = 120.0, *, width: int | None = None) -> str:
        if self.provider in OPENAI_COMPAT_PROVIDERS:
            return self._chat_openai_compat(user_msg, timeout, width=width)
        if self.provider == "claude":
            return self._chat_claude(user_msg, timeout, width=width)
        if self.provider == "gemini":
            return self._chat_gemini(user_msg, timeout, width=width)
        return self._chat_ollama(user_msg, timeout, width=width)

    def _one_shot_chat(self, system: str, user: str, timeout: float = 120.0) -> str:
        """Chat sin historial ni estado de partida (para generar prompts)."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if self.provider in OPENAI_COMPAT_PROVIDERS:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": min(1.0, max(0.4, self.temperature)),
                "max_tokens": 1800,
            }
            headers = openai_compat_headers(self.api_key, self.provider)
            data = self._post_json(
                openai_chat_url(self.api_base), payload, headers, timeout
            )
            return extract_openai_text(data)
        if self.provider == "claude":
            payload = build_claude_payload(
                self.model, system, messages, min(1.0, max(0.4, self.temperature)), 1800
            )
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_VERSION,
            }
            data = self._post_json(claude_url(self.api_base), payload, headers, timeout)
            return extract_claude_text(data)
        if self.provider == "gemini":
            if not self.api_key.strip():
                raise RuntimeError("Falta API key de Gemini.")
            payload = build_gemini_payload(
                system, messages, min(1.0, max(0.4, self.temperature)), 1800
            )
            url = gemini_url(self.api_base, self.model)
            url = f"{url}?key={urllib.parse.quote(self.api_key, safe='')}"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }
            data = self._post_json(url, payload, headers, timeout)
            text = extract_gemini_text(data)
            if not text.strip():
                raise RuntimeError(f"Gemini respondio vacio: {json.dumps(data)[:300]}")
            return text
        # ollama
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": min(1.0, max(0.4, self.temperature)),
                "num_predict": 1800,
            },
        }
        data = self._post_json(
            self.ollama_url,
            payload,
            {"Content-Type": "application/json"},
            timeout,
        )
        return data["message"]["content"]

    def generate_system_prompt(self, timeout: float = 120.0) -> dict[str, Any]:
        """Genera system prompt + estado inicial (no modifica self hasta Guardar)."""
        raw = self._one_shot_chat(_PROMPT_GEN_SYSTEM, _PROMPT_GEN_USER, timeout=timeout)
        return parse_generated_bundle(raw)

    def intro_packet(
        self,
        use_llm: bool = True,
        timeout: float = 120.0,
        *,
        width: int | None = None,
    ) -> str:
        """Resumen de arranque = bloque MUNDO DE ESTA PARTIDA (sin LLM)."""
        del use_llm, timeout  # API estable; el resumen ya no llama al modelo
        w = clamp_cols(width)
        st = self.state.to_dict()
        cache_key = (
            f"w={w}\n"
            + self.system.strip()
            + "\n"
            + json.dumps(st, ensure_ascii=True, sort_keys=True)
        )
        if self._intro_packet and self._intro_key == cache_key:
            return self._intro_packet

        packet = build_mundo_intro_packet(self.system, st, width=w)
        self._intro_packet = packet
        self._intro_key = cache_key
        self.last_user = "(intro)"
        self.last_packet = packet
        return packet

    def inventory_packet(self, *, width: int | None = None) -> str:
        w = clamp_cols(width)
        if not self.state.inventory:
            text = "No llevas nada. Las manos vacias."
            sound = 0
        else:
            items = ", ".join(self.state.inventory)
            text = f"Llevas: {items}."
            sound = 3
        packet = packet_from_text(text, sound=sound, error=0, width=w)
        self.last_user = "inventario"
        self.last_packet = packet
        return packet

    def turn(self, user_msg: str, *, width: int | None = None) -> str:
        w = clamp_cols(width)
        user_msg = normalize_cpc(user_msg)[:120] or "miro alrededor"
        self.last_user = user_msg
        self.last_error = ""

        # Comando local: inventario / inv
        low = user_msg.lower().strip()
        if low in ("inventario", "inv", "i", "objetos"):
            return self.inventory_packet(width=w)

        try:
            raw = self._chat(user_msg, width=w)
            if not isinstance(raw, str):
                raise RuntimeError(f"Respuesta LLM invalida (tipo {type(raw).__name__})")
            raw = normalize_protocol_separators(raw)
            raw = self.state.apply_meta_lines(raw)
            packet = repack_llm_text(raw, width=w)
            self.history.append({"role": "user", "content": user_msg})
            # Guardar texto narrativo limpio (no el paquete con metadatos T:/S:/E:)
            # para que el historial que recibe el LLM sea conversación natural
            clean_assistant = " ".join(parse_packet(packet)["lines"])
            self.history.append({"role": "assistant", "content": clean_assistant})
            self._trim_history()
            self.last_packet = packet
            return packet
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            KeyError,
            json.JSONDecodeError,
            IndexError,
            RuntimeError,
            ValueError,
            TypeError,
            AttributeError,
        ) as exc:
            self.last_error = str(exc)
            print(f"LLM error: {exc}")
            packet = packet_from_text(
                "El maestro no responde. Revisa el panel web / LLM.",
                sound=0,
                error=1,
                width=w,
            )
            self.last_packet = packet
            return packet
