"""Tests para cpc_text."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from cpc_text import join_narrative_segments, normalize_cpc, wrap_lines


def test_normalize_removes_accents():
    assert normalize_cpc("\u00a1Hola, Jos\u00e9!") == "!Hola, Jose!"
    assert normalize_cpc("a\u00f1o ni\u00f1o") == "ano nino"


def test_normalize_strips_non_ascii():
    assert "\u20ac" not in normalize_cpc("precio 10\u20ac")
    assert normalize_cpc("caf\u00e9") == "cafe"


def test_normalize_keeps_ascii_punctuation():
    assert normalize_cpc("Hola, mundo. Que tal?") == "Hola, mundo. Que tal?"


def test_normalize_fullwidth_punctuation():
    assert normalize_cpc("Hola\uff0c mundo\uff0e") == "Hola, mundo."


def test_join_restores_period_at_segment_break():
    text = join_narrative_segments(
        ["El panel parpadea en rojo", "Oyes un zumbido lejano", "Que haces?"]
    )
    assert text == "El panel parpadea en rojo. Oyes un zumbido lejano. Que haces?"


def test_join_keeps_mid_sentence_wrap():
    text = join_narrative_segments(
        ["Puedes sentir la ausencia del flujo", "vital en los conductos."]
    )
    assert text == "Puedes sentir la ausencia del flujo vital en los conductos."


def test_join_preserves_existing_period():
    text = join_narrative_segments(["Frase una.", "Frase dos."])
    assert text == "Frase una. Frase dos."


def test_wrap_40_cols():
    text = "Entras en una cueva oscura y el eco responde a tus pasos con fuerza"
    lines = wrap_lines(text, width=40, max_lines=8)
    assert lines
    assert all(len(line) <= 40 for line in lines)
    assert len(lines) <= 8


def test_wrap_empty():
    assert wrap_lines("") == []
    assert wrap_lines("   ") == []
