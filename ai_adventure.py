"""Cliente Ollama + empaquetado CPC para la aventura."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from cpc_text import normalize_cpc, wrap_lines
from protocol import build_packet, packet_from_text, parse_packet

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "llama3.1:8b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

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


def infer_sound(text: str) -> int:
    low = text.lower()
    for keys, code in _SOUND_KEYWORDS:
        if any(k in low for k in keys):
            return code
    return 0


def _extract_packetish(raw: str) -> str:
    """Si el modelo añade basura, intenta aislar bloque T:/S:/E:."""
    raw = raw.strip()
    # Quitar fences markdown
    raw = re.sub(r"```.*?```", "", raw, flags=re.S)
    m = re.search(r"(T:.*?)(?:\n\s*\n|$)", raw, flags=re.I | re.S)
    if m:
        block = m.group(1).strip()
        # Asegurar S y E si estan cerca
        rest = raw[m.end() : m.end() + 80]
        if not re.search(r"^S:", block, re.I | re.M):
            sm = re.search(r"S:\s*(\d)", rest, re.I) or re.search(r"S:\s*(\d)", raw, re.I)
            if sm:
                block += f"\nS:{sm.group(1)}"
        if not re.search(r"^E:", block, re.I | re.M):
            em = re.search(r"E:\s*(\d)", rest, re.I) or re.search(r"E:\s*(\d)", raw, re.I)
            if em:
                block += f"\nE:{em.group(1)}"
            else:
                block += "\nE:0"
        return block
    return raw


def repack_llm_text(raw: str) -> str:
    """Normaliza cualquier salida del LLM al contrato CPC."""
    candidate = _extract_packetish(raw)
    pkt = parse_packet(candidate)
    # Si parse fallo a "Sin texto", tratar raw como narracion libre
    if pkt["lines"] == ["Sin texto"] or pkt["error"] == 1 and "Sin texto" in pkt["lines"][0]:
        text = normalize_cpc(re.sub(r"^T:", "", raw, flags=re.I))
        text = re.sub(r"S:\s*\d", " ", text, flags=re.I)
        text = re.sub(r"E:\s*\d", " ", text, flags=re.I)
        lines = wrap_lines(text, width=40, max_lines=4)
        sound = infer_sound(text)
        return build_packet(lines or ["El maestro duda un momento."], sound=sound, error=0)

    sound = pkt["sound"]
    if sound == 0:
        sound = infer_sound(" ".join(pkt["lines"]))
    # Re-wrap por si el modelo se paso de 40
    joined = " ".join(pkt["lines"])
    lines = wrap_lines(joined, width=40, max_lines=4)
    if not lines:
        lines = pkt["lines"][:4]
        lines = [normalize_cpc(x)[:40] for x in lines if normalize_cpc(x)]
    return build_packet(lines, sound=sound, error=0)


class AdventureAI:
    def __init__(self, model: str = DEFAULT_MODEL, ollama_url: str = OLLAMA_URL) -> None:
        self.model = model
        self.ollama_url = ollama_url
        self.system = load_system_prompt()
        self.history: list[dict[str, str]] = []
        self.max_history = 6  # pares user/assistant (aprox 3 turnos * 2)

    def reset(self) -> None:
        self.history.clear()

    def _chat(self, user_msg: str, timeout: float = 120.0) -> str:
        messages = [{"role": "system", "content": self.system}]
        messages.extend(self.history[-self.max_history :])
        messages.append({"role": "user", "content": user_msg})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 180},
        }
        req = urllib.request.Request(
            self.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["message"]["content"]

    def turn(self, user_msg: str) -> str:
        user_msg = normalize_cpc(user_msg)[:120] or "miro alrededor"
        try:
            raw = self._chat(user_msg)
            packet = repack_llm_text(raw)
            # Guardar historial en forma compacta
            self.history.append({"role": "user", "content": user_msg})
            self.history.append({"role": "assistant", "content": packet.strip()})
            if len(self.history) > self.max_history * 2:
                self.history = self.history[-(self.max_history * 2) :]
            return packet
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            print(f"Ollama error: {exc}")
            return packet_from_text(
                "El maestro no responde. Revisa Ollama en el PC.",
                sound=0,
                error=1,
            )
