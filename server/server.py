"""
Servidor SINTAXIA (CPC HTTP + panel web).

Escucha en 0.0.0.0:8080
  CPC:  GET /ping  /turn?msg=...  /reset
  Web:  GET /ui
  API:  GET/POST /api/config  GET /api/status  POST /api/reset
        GET /api/models  GET /api/saves  POST /api/save  POST /api/load

Uso:
  python server.py
  python server.py --mock
  python server.py --model llama3.1:8b
"""

from __future__ import annotations

import argparse
import atexit
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus, urlparse

from ai_adventure import (
    DEFAULT_MODEL,
    DEFAULT_START_STATE,
    AdventureAI,
    list_ollama_models,
    list_provider_models,
    load_system_prompt,
)
from llm_providers import DEFAULTS as PROV_DEFAULTS
from llm_providers import PROVIDERS
from protocol import build_packet, clamp_cols, packet_from_text, parse_packet


def parse_cols(qs: dict) -> int:
    """Lee ?cols=40|80 (tambien ?w=). Default MODE 1 = 40."""
    raw = (qs.get("cols") or qs.get("w") or ["40"])[0]
    try:
        return clamp_cols(int(raw))
    except (TypeError, ValueError):
        return clamp_cols(40)
from save_game import delete_slot, list_slots, load_slot, save_slot, validate_slot
from settings_store import load_settings, save_settings

HOST = "0.0.0.0"
PORT = 8080
WEB_DIR = Path(__file__).resolve().parent / "web"

# _state_lock: protege lecturas/escrituras de config, mock, reset, saves.
# Solo para operaciones RAPIDAS (milisegundos).
_state_lock = threading.Lock()

# _turn_lock: serializa las llamadas al LLM (que pueden tardar 10-120 s).
# Independiente de _state_lock para que el panel web siga respondiendo
# mientras el CPC espera la respuesta del maestro.
_turn_lock = threading.Lock()

_MOCK_RULES: list[tuple[tuple[str, ...], str, int]] = [
    (("cueva", "caverna", "oscuro"), "Entras en una cueva oscura. El eco responde a tus pasos.", 2),
    (("espada", "arma", "coger", "agarrar"), "Encuentras una espada oxidada. Brillan runas en la hoja.", 3),
    (("luchar", "atacar", "golpear", "matar"), "El enemigo te embiste. Chocan metal y gritos.", 4),
    (("peligro", "trampa", "monstruo", "dragon"), "Sientes peligro. Algo se mueve en la sombra.", 1),
    (("ganar", "victoria", "tesoro", "abrir"), "Has hallado el tesoro. Una luz llena la sala.", 5),
]

_DEFAULT_TEXT = "Estas en una sala de piedra. Hay puertas al norte y al este. Que haces?"
_ai: AdventureAI | None = None
_use_mock = False
_last_mock_packet = ""
_last_mock_user = ""


def turn_reply(user_msg: str, *, width: int | None = None) -> str:
    w = clamp_cols(width)
    # 1) Bloqueo rapido: comandos locales + decidir si es LLM o mock
    with _state_lock:
        ai = ensure_ai()
        low = (user_msg or "").strip().lower()

        if low in ("inventario", "inv", "i", "objetos"):
            return ai.inventory_packet(width=w)

        local = handle_save_load_command(ai, low, width=w)
        if local is not None:
            return local

        if _use_mock or _ai is None:
            return mock_reply(user_msg, width=w)

    # 2) Llamada al LLM fuera del _state_lock para no congelar el servidor.
    #    _turn_lock serializa las llamadas (evita que dos turnos corran a la vez)
    #    pero permite que /ping, /api/config, /api/models, etc. respondan siempre.
    with _turn_lock:
        return ai.turn(user_msg, width=w)


def handle_save_load_command(
    ai: AdventureAI, low: str, *, width: int | None = None
) -> str | None:
    """Comandos locales SAVE/LOAD/SAVES. Devuelve paquete o None."""
    w = clamp_cols(width)
    if low in ("saves", "partidas", "slots"):
        lines: list[str] = []
        for info in list_slots():
            n = info["slot"]
            if info.get("occupied"):
                when = str(info.get("saved_at") or "")[:10]
                name = str(info.get("name") or f"slot{n}")[:10]
                lines.append(f"Slot {n}: {name} {when}")
            else:
                lines.append(f"Slot {n}: (vacio)")
        packet = build_packet(lines, sound=0, error=0, width=w)
        ai.last_user = "saves"
        ai.last_packet = packet
        return packet

    m = re.match(r"^(save|guardar)\s*([123])$", low)
    if m:
        slot = int(m.group(2))
        try:
            save_slot(ai, slot)
            packet = packet_from_text(
                f"Partida guardada en slot {slot}.", sound=5, error=0, width=w
            )
        except Exception as exc:
            packet = packet_from_text(
                f"No se pudo guardar: {exc}", sound=0, error=1, width=w
            )
        ai.last_user = f"save {slot}"
        ai.last_packet = packet
        return packet

    m = re.match(r"^(load|cargar)\s*([123])$", low)
    if m:
        slot = int(m.group(2))
        try:
            load_slot(ai, slot)
            inv = ", ".join(ai.state.inventory) if ai.state.inventory else "(vacio)"
            packet = packet_from_text(
                f"Cargado slot {slot}. {ai.state.location}. Llevas: {inv}.",
                sound=0,
                error=0,
                width=w,
            )
            ai.last_packet = packet
        except FileNotFoundError:
            packet = packet_from_text(f"Slot {slot} vacio.", sound=0, error=1, width=w)
            ai.last_packet = packet
        except Exception as exc:
            packet = packet_from_text(
                f"Error al cargar: {exc}", sound=0, error=1, width=w
            )
            ai.last_packet = packet
        ai.last_user = f"load {slot}"
        return packet

    return None


def mock_reply(user_msg: str, *, width: int | None = None) -> str:
    global _last_mock_packet, _last_mock_user
    w = clamp_cols(width)
    ai = ensure_ai()
    msg = (user_msg or "").lower()
    _last_mock_user = user_msg
    for keys, text, sound in _MOCK_RULES:
        if any(k in msg for k in keys):
            if any(k in msg for k in ("espada", "arma", "coger", "agarrar")):
                if "espada" not in ai.state.inventory:
                    ai.state.inventory.append("espada")
            if any(k in msg for k in ("tesoro", "abrir")):
                ai.state.flags["tesoro"] = True
            packet = packet_from_text(text, sound=sound, error=0, width=w)
            _last_mock_packet = packet
            ai.last_packet = packet
            ai.last_user = user_msg
            return packet
    packet = packet_from_text(_DEFAULT_TEXT, sound=0, error=0, width=w)
    _last_mock_packet = packet
    ai.last_packet = packet
    ai.last_user = user_msg
    return packet


def ensure_ai() -> AdventureAI:
    global _ai
    if _ai is None:
        _ai = AdventureAI()
    return _ai


class AdventureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_plain(self, body: str, status: int = 200) -> None:
        self._send(body.encode("ascii", errors="replace"), "text/plain; charset=ascii", status)

    def _send_json(self, obj: object, status: int = 200) -> None:
        data = json.dumps(obj, ensure_ascii=True, indent=2).encode("utf-8")
        self._send(data, "application/json; charset=utf-8", status)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        if path in ("/ui", "/ui/"):
            html_path = WEB_DIR / "ui.html"
            if not html_path.is_file():
                self._send_plain("UI no encontrada", 404)
                return
            self._send(html_path.read_bytes(), "text/html; charset=utf-8")
            return

        if path.startswith("/assets/"):
            name = path[len("/assets/") :]
            if "/" in name or "\\" in name or name.startswith("."):
                self._send_plain("Bad path", 400)
                return
            asset = WEB_DIR / name
            if not asset.is_file():
                self._send_plain("Not found", 404)
                return
            ctype = "application/octet-stream"
            if name.endswith(".png"):
                ctype = "image/png"
            elif name.endswith(".jpg") or name.endswith(".jpeg"):
                ctype = "image/jpeg"
            elif name.endswith(".css"):
                ctype = "text/css; charset=utf-8"
            elif name.endswith(".js"):
                ctype = "application/javascript; charset=utf-8"
            self._send(asset.read_bytes(), ctype)
            return

        if path == "/api/status":
            self._send_json(
                {
                    "ok": True,
                    "mock": _use_mock,
                    "port": PORT,
                }
            )
            return

        if path == "/api/config":
            with _state_lock:
                ai = ensure_ai()
                cfg = ai.config_dict()
                if _use_mock:
                    cfg["last_user"] = _last_mock_user or cfg.get("last_user", "")
                    cfg["last_packet"] = _last_mock_packet or cfg.get("last_packet", "")
            self._send_json(cfg)
            return

        if path == "/api/models":
            provider = qs.get("provider", ["ollama"])[0]
            api_base  = unquote_plus(qs.get("api_base", [""])[0])
            api_key   = unquote_plus(qs.get("api_key",  [""])[0])
            # Si no nos pasan api_key pero el AI ya tiene una cargada, la usamos
            with _state_lock:
                ai_now = ensure_ai()
                if not api_key and ai_now.api_key:
                    api_key = ai_now.api_key
                if not api_base and ai_now.api_base:
                    api_base = ai_now.api_base
                ollama_url = ai_now.ollama_url
            print(f"MODELS provider={provider!r} api_base={api_base!r} ollama_url={ollama_url!r} key={'*' if api_key else '(none)'}")
            try:
                models = list_provider_models(
                    provider=provider,
                    api_base=api_base,
                    api_key=api_key,
                    ollama_url=ollama_url,
                )
                print(f"MODELS ok → {len(models)} modelos")
                self._send_json({"ok": True, "models": models, "provider": provider})
            except Exception as exc:
                print(f"MODELS error: {exc}")
                self._send_json({"ok": False, "models": [], "error": str(exc), "provider": provider})
            return

        if path == "/api/saves":
            self._send_json({"slots": list_slots()})
            return

        if path == "/api/default_prompt":
            try:
                system = load_system_prompt()
                self._send_json(
                    {
                        "ok": True,
                        "system": system,
                        "state": dict(DEFAULT_START_STATE),
                    }
                )
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 500)
            return

        if path == "/ping":
            cols = parse_cols(qs)
            with _state_lock:
                mode = "mock" if _use_mock else "ollama"
                if not _use_mock and _ai is not None:
                    mode = _ai.provider
            body = packet_from_text(f"OK servidor {mode}", sound=0, error=0, width=cols)
            self._send_plain(body)
            return

        if path == "/intro":
            cols = parse_cols(qs)
            with _state_lock:
                use_mock = _use_mock
                ai = ensure_ai()
            with _turn_lock:
                print(f"INTRO mock={use_mock} provider={ai.provider} cols={cols}")
                body = ai.intro_packet(use_llm=not use_mock, width=cols)
            self._send_plain(body)
            return

        if path == "/reset":
            cols = parse_cols(qs)
            with _state_lock:
                if _ai is not None:
                    body = _ai.reset(width=cols)
                else:
                    body = packet_from_text(
                        "Partida reiniciada.",
                        sound=0,
                        error=0,
                        width=cols,
                    )
            self._send_plain(body)
            return

        if path == "/turn":
            cols = parse_cols(qs)
            raw_msg = qs.get("msg", [""])[0]
            msg = unquote_plus(raw_msg)[:120]
            print(f"TURN cols={cols}: {msg!r}")
            body = turn_reply(msg, width=cols)
            parse_packet(body)
            self._send_plain(body)
            return

        if path == "/":
            # Redirigir al panel
            self.send_response(302)
            self.send_header("Location", "/ui")
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
            return

        self._send_plain(
            packet_from_text("Ruta desconocida", sound=0, error=1),
            status=404,
        )

    def do_POST(self) -> None:  # noqa: N802
        global _use_mock
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/config":
            data = self._read_json()
            with _state_lock:
                if "mock" in data:
                    _use_mock = bool(data["mock"])
                ai = ensure_ai()
                ai.apply_config(data)
                cfg = ai.config_dict()
                cfg["mock"] = _use_mock
                save_settings(ai, mock=_use_mock)
            print(f"CONFIG mock={_use_mock} provider={ai.provider} model={ai.model}")
            self._send_json({"ok": True, "config": cfg})
            return

        if path == "/api/reset":
            with _state_lock:
                if _ai is not None:
                    body = _ai.reset()
                else:
                    body = packet_from_text(
                        "Partida reiniciada.",
                        sound=0,
                        error=0,
                    )
            self._send_json({"ok": True, "packet": body})
            return

        if path == "/api/save":
            data = self._read_json()
            with _state_lock:
                ai = ensure_ai()
                try:
                    slot = validate_slot(data.get("slot", 1))
                    name = data.get("name")
                    payload = save_slot(ai, slot, name=str(name) if name else None)
                    self._send_json({"ok": True, "save": payload, "slots": list_slots()})
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 400)
            return

        if path == "/api/load":
            data = self._read_json()
            with _state_lock:
                ai = ensure_ai()
                try:
                    slot = validate_slot(data.get("slot", 1))
                    payload = load_slot(ai, slot)
                    self._send_json(
                        {
                            "ok": True,
                            "save": payload,
                            "state": ai.state.to_dict(),
                            "packet": ai.last_packet,
                            "slots": list_slots(),
                        }
                    )
                except FileNotFoundError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 404)
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 400)
            return

        if path == "/api/delete_save":
            data = self._read_json()
            with _state_lock:
                try:
                    slot = validate_slot(data.get("slot", 1))
                    deleted = delete_slot(slot)
                    self._send_json({"ok": True, "deleted": deleted, "slots": list_slots()})
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 400)
            return

        if path == "/api/generate_prompt":
            with _state_lock:
                if _use_mock:
                    self._send_json(
                        {
                            "ok": False,
                            "error": "Desactiva MOCK y guarda un proveedor IA antes de generar.",
                        },
                        400,
                    )
                    return
                ai = ensure_ai()
            # LLM lento: fuera de _state_lock, serializado con _turn_lock
            with _turn_lock:
                try:
                    print(f"GENERATE_PROMPT provider={ai.provider} model={ai.model}")
                    bundle = ai.generate_system_prompt()
                    self._send_json(
                        {
                            "ok": True,
                            "system": bundle["system"],
                            "state": bundle["state"],
                        }
                    )
                except Exception as exc:
                    print(f"GENERATE_PROMPT error: {exc}")
                    self._send_json({"ok": False, "error": str(exc)}, 500)
            return

        self._send_json({"ok": False, "error": "not found"}, 404)


def get_lan_ip() -> str:
    """Devuelve la IP IPv4 local del PC en la LAN (ej. 192.168.1.4)."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _persist_settings() -> None:
    """Respaldo al cerrar el proceso."""
    if _ai is None:
        return
    save_settings(_ai, mock=_use_mock)


def main() -> None:
    global _ai, _use_mock

    parser = argparse.ArgumentParser(description="Servidor SINTAXIA")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument(
        "--model",
        default=None,
        help="Modelo inicial (si no se pasa, usa settings.json o el tipico del proveedor)",
    )
    parser.add_argument("--mock", action="store_true", help="Arrancar en modo mock")
    parser.add_argument(
        "--provider",
        choices=("ollama", "openai", "claude", "gemini", "openai_compat", "openrouter"),
        default=None,
        help="Proveedor LLM inicial (si no se pasa, usa settings.json o ollama)",
    )
    parser.add_argument(
        "--api-base",
        default=None,
        help="Base URL API (OpenAI/Claude/Gemini/compat/OpenRouter)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (tambien se guarda en server/settings.json local)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="No abrir el panel /ui en el navegador al arrancar",
    )
    args = parser.parse_args()

    saved = load_settings()
    if saved:
        print("SETTINGS cargados desde settings.json")

    provider = args.provider or str(saved.get("provider") or "ollama")
    if provider not in PROVIDERS:
        provider = "ollama"
    preset = PROV_DEFAULTS.get(provider) or {}
    model = args.model or str(saved.get("model") or "") or str(
        preset.get("model") or DEFAULT_MODEL
    )

    _ai = AdventureAI(model=model, provider=provider)
    apply_from_file = {
        k: saved[k]
        for k in (
            "ollama_url",
            "api_base",
            "api_key",
            "temperature",
            "system",
            "start_state",
        )
        if k in saved
    }
    if apply_from_file:
        _ai.apply_config(apply_from_file)

    if args.api_base is not None:
        _ai.apply_config({"api_base": args.api_base})
    elif "api_base" not in saved:
        preset_base = preset.get("api_base") or ""
        if preset_base:
            _ai.api_base = preset_base.rstrip("/")

    if args.api_key is not None:
        _ai.apply_config({"api_key": args.api_key})

    _use_mock = bool(saved.get("mock")) if saved else False
    if args.mock:
        _use_mock = True

    atexit.register(_persist_settings)

    if _use_mock:
        print("Modo MOCK (sin LLM)")
    else:
        print(
            f"LLM provider={_ai.provider} model={_ai.model} "
            f"key={'*' if _ai.api_key else '(none)'}"
        )

    server = ThreadingHTTPServer((args.host, args.port), AdventureHandler)
    lan_ip = get_lan_ip()
    ui_url = f"http://127.0.0.1:{args.port}/ui"
    print(f"Servidor en todas las interfaces (0.0.0.0:{args.port})")
    print(f"Panel web (PC): {ui_url}")
    print(f"CPC (Wi-Fi LAN): http://{lan_ip}:{args.port}/ (pon P$=\"{lan_ip}:{args.port}\" en BASIC)")

    if not args.no_browser:
        # Tras un instante para que el socket ya este escuchando
        def _open_ui() -> None:
            import webbrowser

            webbrowser.open(ui_url)

        threading.Timer(0.6, _open_ui).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")
    finally:
        _persist_settings()
        server.server_close()


if __name__ == "__main__":
    main()
