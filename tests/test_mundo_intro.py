"""Tests resumen inicial MUNDO DE ESTA PARTIDA."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from ai_adventure import (
    build_mundo_intro_lines,
    build_mundo_intro_packet,
    parse_mundo_fields,
)
from protocol import parse_packet


SAMPLE = """
Eres el Master de una aventura de texto clasica para Amstrad CPC (1984).

MUNDO DE ESTA PARTIDA:
- Titulo/tema: Estacion Abisal 9
- Premisa: Eres el unico tecnico despierto en una estacion submarina que se esta inundando. Las compuertas automaticas han fallado y el oceano presiona contra el cristal. Debes restablecer la energia antes de que la presion aplaste los mamparos.
- Tono: claustrofobia, presion, tecnologia obsoleta, urgencia
- El jugador empieza en: sala de control principal
- Inventario inicial: linterna, llave inglesa
- Gancho: El agua helada ya cubre tus tobillos y la alarma roja parpadea en la oscuridad.

REGLAS DE NARRATIVA Y COHERENCIA:
- Manten continuidad.
"""


def test_parse_mundo_fields():
    f = parse_mundo_fields(SAMPLE)
    assert f["title"] == "Estacion Abisal 9"
    assert "tecnico" in f["premise"]
    assert "claustrofobia" in f["tone"]
    assert f["location"] == "sala de control principal"
    assert "linterna" in f["inventory"]
    assert "tobillos" in f["hook"]


def test_build_mundo_intro_includes_full_premise():
    lines = build_mundo_intro_lines(SAMPLE)
    blob = " ".join(lines)
    assert "MUNDO" in lines[0]
    assert "Abisal" in blob or "Titulo" in blob
    # Premisa completa (sin truncar con ...)
    assert "inundando" in blob
    assert "mamparos" in blob
    assert "..." not in blob
    assert all(len(L) <= 40 for L in lines)


def test_intro_packet_no_llm_shape():
    raw = build_mundo_intro_packet(SAMPLE)
    assert "..." not in raw
    pkt = parse_packet(raw, max_lines=80)
    assert pkt["error"] == 0
    assert pkt["sound"] == 2
    assert "MUNDO" in pkt["lines"][0]
    blob = " ".join(pkt["lines"])
    assert "mamparos" in blob
