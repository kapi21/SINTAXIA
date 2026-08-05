"""Tests save/load de partidas."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from ai_adventure import AdventureAI, DEFAULT_START_STATE
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
    ai.system = (
        "MUNDO DE ESTA PARTIDA:\n"
        "- Titulo/tema: Cripta Test\n"
        "- Premisa: Exploras una cripta sellada bajo la colina.\n"
        "- Tono: misterio, frio\n"
        "- El jugador empieza en: entrada cripta\n"
        "- Inventario inicial: (vacio)\n"
        "- Gancho: La antorcha parpadea.\n"
        "\nREGLAS DE NARRATIVA:\n- ok\n"
    )
    ai.start_state = {
        "location": "entrada cripta",
        "inventory": [],
        "flags": {"antorcha_apagada": True},
    }
    ai.state.location = "cripta"
    ai.state.inventory = ["llave", "antorcha"]
    ai.state.flags["puerta"] = True
    ai.history = [
        {"role": "user", "content": "abro la puerta"},
        {"role": "assistant", "content": "La puerta cruje y ves un pasillo humedo."},
    ]
    save_slot(ai, 1, name="prueba", base=tmp_path)
    raw = json.loads((tmp_path / "slot1.json").read_text(encoding="utf-8"))
    assert "Cripta Test" in raw["system"]
    assert raw["start_state"]["location"] == "entrada cripta"

    slots = list_slots(base=tmp_path)
    assert slots[0]["occupied"] is True
    assert slots[0]["name"] == "prueba"
    assert slots[1]["occupied"] is False

    ai2 = AdventureAI()
    ai2.system = "OTRO MUNDO"
    ai2.start_state = dict(DEFAULT_START_STATE)
    load_slot(ai2, 1, base=tmp_path)
    assert ai2.state.location == "cripta"
    assert ai2.state.inventory == ["llave", "antorcha"]
    assert ai2.state.flags.get("puerta") is True
    assert len(ai2.history) == 2
    assert "Cripta Test" in ai2.system
    assert ai2.start_state["location"] == "entrada cripta"
    assert ai2.start_state["flags"].get("antorcha_apagada") is True
    pkt = ai2.last_packet.lower()
    assert "cargado" in pkt or "partida cargada" in pkt
    assert "cripta" in pkt
    assert "llave" in pkt or "antorcha" in pkt
    assert "mundo" in pkt or "premisa" in pkt
    assert "ultima accion" in pkt or "maestro" in pkt or "hasta ahora" in pkt


def test_load_resume_lines_include_world_and_recap():
    from ai_adventure import build_load_resume_lines

    system = (
        "MUNDO DE ESTA PARTIDA:\n"
        "- Titulo/tema: Estacion Abisal\n"
        "- Premisa: La estacion se inunda y debes restaurar energia.\n"
        "- Tono: urgencia\n"
        "- El jugador empieza en: sala control\n"
        "- Inventario inicial: linterna\n"
        "- Gancho: El agua sube.\n"
    )
    state = {"location": "mamparo 3", "inventory": ["linterna", "llave"], "flags": {"escudos": True}}
    history = [
        {"role": "user", "content": "abro la valvula"},
        {"role": "assistant", "content": "El agua deja de subir un momento."},
    ]
    lines = build_load_resume_lines(system, state, history, had_system=True, slot=2, width=40)
    blob = " ".join(lines).lower()
    assert "slot 2" in blob
    assert "abisal" in blob or "mundo" in blob
    assert "mamparo" in blob
    assert "linterna" in blob
    assert "valvula" in blob or "maestro" in blob
    assert len(lines) <= 12


def test_load_legacy_without_system_keeps_current_world(tmp_path):
    path = tmp_path / "slot2.json"
    path.write_text(
        json.dumps(
            {
                "slot": 2,
                "name": "viejo",
                "saved_at": "2026-01-01T00:00:00Z",
                "state": {"location": "sala", "inventory": ["cuerda"], "flags": {}},
                "history": [{"role": "user", "content": "hola"}],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    ai = AdventureAI()
    ai.system = "MUNDO ACTUAL EN MEMORIA"
    ai.start_state = {"location": "base", "inventory": ["x"], "flags": {}}
    load_slot(ai, 2, base=tmp_path)
    assert ai.state.location == "sala"
    assert ai.state.inventory == ["cuerda"]
    assert ai.system == "MUNDO ACTUAL EN MEMORIA"
    assert ai.start_state["location"] == "base"
    assert "no embebido" in ai.last_packet.lower() or "Mundo no" in ai.last_packet


def test_load_empty_raises(tmp_path):
    ai = AdventureAI()
    try:
        load_slot(ai, 2, base=tmp_path)
        assert False
    except FileNotFoundError:
        pass
