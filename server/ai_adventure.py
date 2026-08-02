"""Cliente LLM (Ollama, OpenAI, Claude, Gemini, OpenAI-compatible) + empaquetado CPC."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from cpc_text import normalize_cpc, wrap_lines
from game_state import GameState
from llm_providers import (
    ANTHROPIC_VERSION,
    DEFAULTS,
    PROVIDERS,
    build_claude_payload,
    build_gemini_payload,
    claude_url,
    extract_claude_text,
    extract_gemini_text,
    extract_openai_text,
    gemini_url,
    openai_chat_url,
)
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
    - openai/compat → GET {api_base}/models (Bearer api_key)
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

        if provider in ("openai", "openai_compat"):
            if not api_base:
                from llm_providers import DEFAULTS
                api_base = DEFAULTS.get(provider, {}).get("api_base", "https://api.openai.com/v1")
            url = api_base.rstrip("/") + "/models"
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
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

    def export_save(self) -> dict[str, Any]:
        hist = self.history[-(self.max_history * 2) :]
        clean_hist: list[dict[str, str]] = []
        for item in hist:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", ""))
            content = str(item.get("content", ""))
            if role in ("user", "assistant") and content:
                clean_hist.append({"role": role, "content": content[:500]})
        return {
            "state": self.state.to_dict(),
            "history": clean_hist,
        }

    def import_save(self, data: dict[str, Any]) -> None:
        self.state = GameState.from_dict(data.get("state") if isinstance(data, dict) else None)
        self.history = []
        hist = data.get("history") if isinstance(data, dict) else None
        if isinstance(hist, list):
            for item in hist[-(self.max_history * 2) :]:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role", ""))
                content = str(item.get("content", ""))
                if role in ("user", "assistant") and content:
                    self.history.append({"role": role, "content": content[:500]})
        self.last_error = ""
        self.last_user = "(load)"
        inv = ", ".join(self.state.inventory) if self.state.inventory else "(vacio)"
        self.last_packet = packet_from_text(
            f"Partida cargada. Lugar: {self.state.location}. Llevas: {inv}.",
            sound=0,
            error=0,
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
            "history_len": len(self.history),
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

    def _chat_ollama(self, user_msg: str, timeout: float = 120.0) -> str:
        payload = {
            "model": self.model,
            "messages": self._messages(user_msg),
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

    def _chat_openai_compat(self, user_msg: str, timeout: float = 120.0) -> str:
        payload = {
            "model": self.model,
            "messages": self._messages(user_msg),
            "temperature": self.temperature,
            "max_tokens": 500,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = self._post_json(
            openai_chat_url(self.api_base), payload, headers, timeout
        )
        return extract_openai_text(data)

    def _chat_claude(self, user_msg: str, timeout: float = 120.0) -> str:
        messages = self._messages(user_msg)
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

    def _chat_gemini(self, user_msg: str, timeout: float = 120.0) -> str:
        if not self.api_key.strip():
            raise RuntimeError("Falta API key de Gemini. Pegala en el panel y pulsa Guardar.")
        messages = self._messages(user_msg)
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

    def _chat(self, user_msg: str, timeout: float = 120.0) -> str:
        if self.provider in ("openai", "openai_compat"):
            return self._chat_openai_compat(user_msg, timeout)
        if self.provider == "claude":
            return self._chat_claude(user_msg, timeout)
        if self.provider == "gemini":
            return self._chat_gemini(user_msg, timeout)
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
            # Guardar texto narrativo limpio (no el paquete con metadatos T:/S:/E:)
            # para que el historial que recibe el LLM sea conversación natural
            clean_assistant = " ".join(parse_packet(packet)["lines"])
            self.history.append({"role": "assistant", "content": clean_assistant})
            if len(self.history) > self.max_history * 2:
                self.history = self.history[-(self.max_history * 2) :]
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
        ) as exc:
            self.last_error = str(exc)
            print(f"LLM error: {exc}")
            packet = packet_from_text(
                "El maestro no responde. Revisa el panel web / LLM.",
                sound=0,
                error=1,
            )
            self.last_packet = packet
            return packet
