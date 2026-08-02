"""Tests para protocol."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from protocol import build_packet, parse_packet, packet_from_text


def test_build_and_parse_roundtrip():
    raw = build_packet(["Entras en una cueva oscura.", "Hace frio."], sound=2, error=0)
    assert raw.startswith("T:")
    assert "S:2" in raw
    assert "E:0" in raw
    pkt = parse_packet(raw)
    assert pkt["sound"] == 2
    assert pkt["error"] == 0
    assert len(pkt["lines"]) == 2
    assert "cueva" in pkt["lines"][0].lower()


def test_sound_clamped():
    raw = build_packet(["X"], sound=99, error=0)
    assert "S:5" in raw
    raw = build_packet(["X"], sound=-3, error=0)
    assert "S:0" in raw


def test_packet_from_text_wraps():
    long_text = "Palabra " * 20
    raw = packet_from_text(long_text, sound=3)
    pkt = parse_packet(raw)
    assert pkt["sound"] == 3
    assert all(len(line) <= 40 for line in pkt["lines"])


def test_parse_tolerates_crlf():
    raw = "T:Hola|Mundo\r\nS:1\r\nE:0\r\n"
    pkt = parse_packet(raw)
    assert pkt["lines"] == ["Hola", "Mundo"]
    assert pkt["sound"] == 1


def test_twelve_lines_and_multi_t_rows():
    lines = [f"Linea numero {i} de texto." for i in range(1, 13)]
    raw = build_packet(lines, sound=2, error=0)
    assert raw.count("T:") >= 2
    for part in raw.split("\r\n"):
        if part.startswith("T:"):
            assert len(part) <= 252  # "T:" + <=250
    pkt = parse_packet(raw)
    assert len(pkt["lines"]) == 12
    assert pkt["lines"][0].startswith("Linea numero 1")
    assert pkt["lines"][-1].startswith("Linea numero 12")


def test_thirteenth_line_truncated():
    lines = [f"L{i} xxxxxxxxxx" for i in range(1, 15)]
    raw = build_packet(lines, sound=0, error=0)
    pkt = parse_packet(raw)
    assert len(pkt["lines"]) == 12
    assert pkt["lines"][-1].endswith("...")
