"""
Servidor aventura CPC/M4 (Fase 4: Ollama).

Escucha en 0.0.0.0:8080
  GET /ping
  GET /turn?msg=...
  GET /reset

Uso:
  python server.py
  python server.py --mock
  python server.py --model llama3.1:8b
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote_plus, urlparse

from ai_adventure import DEFAULT_MODEL, AdventureAI
from protocol import packet_from_text, parse_packet

HOST = "0.0.0.0"
PORT = 8080

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


def mock_reply(user_msg: str) -> str:
    msg = (user_msg or "").lower()
    for keys, text, sound in _MOCK_RULES:
        if any(k in msg for k in keys):
            return packet_from_text(text, sound=sound, error=0)
    return packet_from_text(_DEFAULT_TEXT, sound=0, error=0)


def turn_reply(user_msg: str) -> str:
    if _use_mock or _ai is None:
        return mock_reply(user_msg)
    return _ai.turn(user_msg)


class AdventureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def _send_plain(self, body: str, status: int = 200) -> None:
        data = body.encode("ascii", errors="replace")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=ascii")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        if path == "/ping":
            mode = "mock" if _use_mock else "ollama"
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
            mode = "mock" if _use_mock else "ollama"
            help_txt = (
                f"Aventura CPC/M4 ({mode})\n"
                "GET /ping\n"
                "GET /turn?msg=miro+alrededor\n"
                "GET /reset\n"
            )
            self._send_plain(help_txt)
            return

        self._send_plain(
            packet_from_text("Ruta desconocida", sound=0, error=1),
            status=404,
        )


def main() -> None:
    global _ai, _use_mock

    parser = argparse.ArgumentParser(description="Servidor aventura CPC/M4")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modelo Ollama")
    parser.add_argument("--mock", action="store_true", help="Sin IA, solo reglas fijas")
    args = parser.parse_args()

    _use_mock = args.mock
    if not _use_mock:
        _ai = AdventureAI(model=args.model)
        print(f"Ollama model: {args.model}")
    else:
        print("Modo MOCK (sin Ollama)")

    server = ThreadingHTTPServer((args.host, args.port), AdventureHandler)
    print(f"Servidor en http://{args.host}:{args.port}/")
    print("Endpoints: /ping  /turn?msg=...  /reset")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
