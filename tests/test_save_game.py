"""Tests save/load de partidas."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from ai_adventure import AdventureAI
from save_game import list_slots, load_slot, save_slot, validate_slot


def test_validate_slot():
    assert validate_slot(1) == 1
    assert validate_slot("3") == 3
    try:
        validate_slot(0)
        assert False
    except ValueError:
        pass


def test_save_load_roundtrip(tmp_path):
    ai = AdventureAI()
    ai.state.location = "cripta"
    ai.state.inventory = ["llave", "antorcha"]
    ai.state.flags["puerta"] = True
    ai.history = [
        {"role": "user", "content": "miro"},
        {"role": "assistant", "content": "T:Oscuridad.\nS:2\nE:0"},
    ]
    save_slot(ai, 1, name="prueba", base=tmp_path)
    slots = list_slots(base=tmp_path)
    assert slots[0]["occupied"] is True
    assert slots[0]["name"] == "prueba"
    assert slots[1]["occupied"] is False

    ai2 = AdventureAI()
    load_slot(ai2, 1, base=tmp_path)
    assert ai2.state.location == "cripta"
    assert ai2.state.inventory == ["llave", "antorcha"]
    assert ai2.state.flags.get("puerta") is True
    assert len(ai2.history) == 2


def test_load_empty_raises(tmp_path):
    ai = AdventureAI()
    try:
        load_slot(ai, 2, base=tmp_path)
        assert False
    except FileNotFoundError:
        pass
