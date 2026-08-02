"""Tests para game_state."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from game_state import GameState


def test_inventory_plus_minus():
    g = GameState()
    rest = g.apply_meta_lines("T:Hola\nI:+llave\nS:3\nE:0\n")
    assert "llave" in g.inventory
    assert "I:" not in rest
    g.apply_meta_lines("I:-llave\n")
    assert g.inventory == []


def test_location_and_flags():
    g = GameState()
    g.apply_meta_lines("L:cripta\nF:puerta_abierta=1\n")
    assert g.location == "cripta"
    assert g.flags["puerta_abierta"] is True


def test_full_inventory_list():
    g = GameState()
    g.apply_meta_lines("I:antorcha, mapa, llave\n")
    assert g.inventory == ["antorcha", "mapa", "llave"]
