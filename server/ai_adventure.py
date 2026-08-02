"""Cliente LLM (Ollama / API OpenAI-compatible) + empaquetado CPC."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from cpc_text import normalize_cpc, wrap_lines
from game_state import GameState
from protocol import CPC_MAX_LINES, CPC_WIDTH, build_packet, packet_from_text, parse_packet

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


def infer_sound(text: str) -> int:
    low = text.lower()
    for keys, code in _SOUND_KEYWORDS:
        if any(k in low for k in keys):
            return code
    return 0


def _extract_packetish(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"```.*?```", "", raw, flags=re.S)
    m = re.search(r"(T:.*?)(?:\n\s*\n|$)", raw, flags=re.I | re.S)
    if m:
        block = m.group(1).strip()
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
    candidate = _extract_packetish(raw)
    pkt = parse_packet(candidate)
    if pkt["lines"] == ["Sin texto"] or (
        pkt["error"] == 1 and pkt["lines"] and "Sin texto" in pkt["lines"][0]
    ):
        text = normalize_cpc(re.sub(r"^T:", "", raw, flags=re.I))
        text = re.sub(r"S:\s*\d", " ", text, flags=re.I)
        text = re.sub(r"E:\s*\d", " ", text, flags=re.I)
        lines = wrap_lines(text, width=CPC_WIDTH, max_lines=CPC_MAX_LINES)
        sound = infer_sound(text)
        return build_packet(lines or ["El maestro duda un momento."], sound=sound, error=0)

    sound = pkt["sound"]
    if sound == 0:
        sound = infer_sound(" ".join(pkt["lines"]))
    joined = " ".join(pkt["lines"])
    lines = wrap_lines(joined, width=CPC_WIDTH, max_lines=CPC_MAX_LINES)
    if not lines:
        lines = pkt["lines"][:CPC_MAX_LINES]
        lines = [normalize_cpc(x)[:CPC_WIDTH] for x in lines if normalize_cpc(x)]
    return build_packet(lines, sound=sound, error=0)


def list_ollama_models(tags_url: str = "http://127.0.0.1:11434/api/tags") -> list[str]:
    try:
        with urllib.request.urlopen(tags_url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


class AdventureAI:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        provider: str = "ollama",
        ollama_url: str = DEFAULT_OLLAMA_CHAT,
        openai_base: str = DEFAULT_OPENAI_BASE,
        api_key: str = "",
        temperature: float = 0.7,
        system: str | None = None,
    ) -> None:
        self.model = model
        self.provider = provider  # ollama | openai
        self.ollama_url = ollama_url
        self.openai_base = openai_base.rstrip("/")
        self.api_key = api_key
        self.temperature = temperature
        self.system = system if system is not None else load_system_prompt()
        self.history: list[dict[str, str]] = []
        self.max_history = 6
        self.state = GameState()
        self.last_user = ""
        self.last_packet = ""
        self.last_error = ""

    def reset(self) -> None:
        self.history.clear()
        self.state.reset()
        self.last_user = ""
        self.last_packet = ""
        self.last_error = ""

    def config_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "ollama_url": self.ollama_url,
            "openai_base": self.openai_base,
            "api_key_set": bool(self.api_key),
            "temperature": self.temperature,
            "system": self.system,
            "history_len": len(self.history),
            "last_user": self.last_user,
            "last_packet": self.last_packet,
            "last_error": self.last_error,
            "state": self.state.to_dict(),
        }

    def apply_config(self, data: dict[str, Any]) -> None:
        if "provider" in data and data["provider"] in ("ollama", "openai"):
            self.provider = data["provider"]
        if "model" in data and str(data["model"]).strip():
            self.model = str(data["model"]).strip()
        if "ollama_url" in data and str(data["ollama_url"]).strip():
            self.ollama_url = str(data["ollama_url"]).strip()
        if "openai_base" in data and str(data["openai_base"]).strip():
            self.openai_base = str(data["openai_base"]).strip().rstrip("/")
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
            self.system = data["system"]

    def _messages(self, user_msg: str) -> list[dict[str, str]]:
        system = self.system + "\n\n" + self.state.summary_for_prompt()
        messages = [{"role": "system", "content": system}]
        messages.extend(self.history[-self.max_history :])
        messages.append({"role": "user", "content": user_msg})
        return messages

    def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _chat_ollama(self, user_msg: str, timeout: float = 120.0) -> str:
        payload = {
            "model": self.model,
            "messages": self._messages(user_msg),
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 220,
            },
        }
        data = self._post_json(
            self.ollama_url,
            payload,
            {"Content-Type": "application/json"},
            timeout,
        )
        return data["message"]["content"]

    def _chat_openai(self, user_msg: str, timeout: float = 120.0) -> str:
        url = f"{self.openai_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self._messages(user_msg),
            "temperature": self.temperature,
            "max_tokens": 220,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = self._post_json(url, payload, headers, timeout)
        return data["choices"][0]["message"]["content"]

    def _chat(self, user_msg: str, timeout: float = 120.0) -> str:
        if self.provider == "openai":
            return self._chat_openai(user_msg, timeout)
        return self._chat_ollama(user_msg, timeout)

    def inventory_packet(self) -> str:
        if not self.state.inventory:
            text = "No llevas nada. Las manos vacias."
            sound = 0
        else:
            items = ", ".join(self.state.inventory)
            text = f"Llevas: {items}."
            sound = 3
        packet = packet_from_text(text, sound=sound, error=0)
        self.last_user = "inventario"
        self.last_packet = packet
        return packet

    def turn(self, user_msg: str) -> str:
        user_msg = normalize_cpc(user_msg)[:120] or "miro alrededor"
        self.last_user = user_msg
        self.last_error = ""

        # Comando local: inventario / inv
        low = user_msg.lower().strip()
        if low in ("inventario", "inv", "i", "objetos"):
            return self.inventory_packet()

        try:
            raw = self._chat(user_msg)
            raw = self.state.apply_meta_lines(raw)
            packet = repack_llm_text(raw)
            self.history.append({"role": "user", "content": user_msg})
            self.history.append({"role": "assistant", "content": packet.strip()})
            if len(self.history) > self.max_history * 2:
                self.history = self.history[-(self.max_history * 2) :]
            self.last_packet = packet
            return packet
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, json.JSONDecodeError, IndexError) as exc:
            self.last_error = str(exc)
            print(f"LLM error: {exc}")
            packet = packet_from_text(
                "El maestro no responde. Revisa el panel web / LLM.",
                sound=0,
                error=1,
            )
            self.last_packet = packet
            return packet
