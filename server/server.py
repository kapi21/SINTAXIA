"""
Servidor SINTAXIA (CPC HTTP + panel web).

Escucha en 0.0.0.0:8080
  CPC:  GET /ping  /turn?msg=...  /reset
  Web:  GET /ui
  API:  GET/POST /api/config  GET /api/status  POST /api/reset  GET /api/models

Uso:
  python server.py
  python server.py --mock
  python server.py --model llama3.1:8b
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus, urlparse

from ai_adventure import DEFAULT_MODEL, AdventureAI, list_ollama_models
from protocol import packet_from_text, parse_packet

HOST = "0.0.0.0"
PORT = 8080
WEB_DIR = Path(__file__).resolve().parent / "web"

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


def turn_reply(user_msg: str) -> str:
    ai = ensure_ai()
    low = (user_msg or "").strip().lower()
    if low in ("inventario", "inv", "i", "objetos"):
        return ai.inventory_packet()
    if _use_mock or _ai is None:
        return mock_reply(user_msg)
    return ai.turn(user_msg)


def mock_reply(user_msg: str) -> str:
    global _last_mock_packet, _last_mock_user
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
            packet = packet_from_text(text, sound=sound, error=0)
            _last_mock_packet = packet
            ai.last_packet = packet
            ai.last_user = user_msg
            return packet
    packet = packet_from_text(_DEFAULT_TEXT, sound=0, error=0)
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
            ai = ensure_ai()
            cfg = ai.config_dict()
            if _use_mock:
                cfg["last_user"] = _last_mock_user or cfg.get("last_user", "")
                cfg["last_packet"] = _last_mock_packet or cfg.get("last_packet", "")
            self._send_json(cfg)
            return

        if path == "/api/models":
            self._send_json({"models": list_ollama_models()})
            return

        if path == "/ping":
            mode = "mock" if _use_mock else "ollama"
            if not _use_mock and _ai is not None:
                mode = _ai.provider
            body = packet_from_text(f"OK servidor {mode}", sound=0, error=0)
            self._send_plain(body)
            return

        if path == "/reset":
            if _ai is not None:
                _ai.reset()
            body = packet_from_text("Nueva partida. Estas en el castillo.", sound=0, error=0)
            self._send_plain(body)
            return

        if path == "/turn":
            raw_msg = qs.get("msg", [""])[0]
            msg = unquote_plus(raw_msg)[:120]
            print(f"TURN: {msg!r}")
            body = turn_reply(msg)
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
            if "mock" in data:
                _use_mock = bool(data["mock"])
            ai = ensure_ai()
            ai.apply_config(data)
            cfg = ai.config_dict()
            cfg["mock"] = _use_mock
            print(f"CONFIG mock={_use_mock} provider={ai.provider} model={ai.model}")
            self._send_json({"ok": True, "config": cfg})
            return

        if path == "/api/reset":
            if _ai is not None:
                _ai.reset()
            body = packet_from_text("Nueva partida. Estas en el castillo.", sound=0, error=0)
            if _ai is not None:
                _ai.last_packet = body
                _ai.last_user = "(reset)"
            self._send_json({"ok": True, "packet": body})
            return

        self._send_json({"ok": False, "error": "not found"}, 404)


def main() -> None:
    global _ai, _use_mock

    parser = argparse.ArgumentParser(description="Servidor SINTAXIA")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modelo inicial")
    parser.add_argument("--mock", action="store_true", help="Arrancar en modo mock")
    parser.add_argument(
        "--provider",
        choices=("ollama", "openai"),
        default="ollama",
        help="Proveedor LLM inicial",
    )
    args = parser.parse_args()

    _use_mock = args.mock
    _ai = AdventureAI(model=args.model, provider=args.provider)
    if _use_mock:
        print("Modo MOCK (sin LLM)")
    else:
        print(f"LLM provider={args.provider} model={args.model}")

    server = ThreadingHTTPServer((args.host, args.port), AdventureHandler)
    print(f"Servidor en http://{args.host}:{args.port}/")
    print(f"Panel web: http://127.0.0.1:{args.port}/ui")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
