"""Tests para cpc_text."""

from cpc_text import normalize_cpc, wrap_lines


def test_normalize_removes_accents():
    # inverted ! -> ! ; accents stripped
    assert normalize_cpc("\u00a1Hola, Jos\u00e9!") == "!Hola, Jose!"
    assert normalize_cpc("a\u00f1o ni\u00f1o") == "ano nino"


def test_normalize_strips_non_ascii():
    assert "\u20ac" not in normalize_cpc("precio 10\u20ac")
    assert normalize_cpc("caf\u00e9") == "cafe"


def test_wrap_40_cols():
    text = "Entras en una cueva oscura y el eco responde a tus pasos con fuerza"
    lines = wrap_lines(text, width=40, max_lines=8)
    assert lines
    assert all(len(line) <= 40 for line in lines)
    assert len(lines) <= 8


def test_wrap_empty():
    assert wrap_lines("") == []
    assert wrap_lines("   ") == []
