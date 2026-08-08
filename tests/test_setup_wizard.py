"""Tests del asistente de configuracion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from ai_adventure import AdventureAI
from save_game import list_slots, save_slot
from settings_store import is_setup_complete, load_settings, save_settings, write_setup_stub
from setup_wizard import (
    SETUP_RESET_PHRASE,
    build_status,
    perform_settings_reset,
    validate_complete_body,
)


def test_is_setup_complete_empty():
    assert is_setup_complete({}) is False
    assert is_setup_complete(None) is False


def test_is_setup_complete_flag():
    assert is_setup_complete({"setup_complete": True}) is True
    assert is_setup_complete({"setup_complete": False, "provider": "ollama", "model": "x"}) is False


def test_is_setup_complete_legacy():
    assert is_setup_complete({"provider": "ollama", "model": "llama3.1:8b"}) is True
    assert is_setup_complete({"mock": True}) is True
    assert is_setup_complete({"provider": "ollama"}) is False


def test_validate_complete_mock_ok():
    body = validate_complete_body({"mock": True, "provider": "ollama", "preferred_port": 8080})
    assert body["mock"] is True
    assert body["preferred_port"] == 8080


def test_validate_complete_needs_key():
    with pytest.raises(ValueError, match="api_key"):
        validate_complete_body(
            {
                "mock": False,
                "provider": "openai",
                "model": "gpt-4o-mini",
                "preferred_port": 8080,
            }
        )


def test_validate_complete_openai_with_key():
    body = validate_complete_body(
        {
            "mock": False,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "sk-test",
            "preferred_port": 9090,
        }
    )
    assert body["api_key"] == "sk-test"
    assert body["preferred_port"] == 9090


def test_validate_port_range():
    with pytest.raises(ValueError, match="rango"):
        validate_complete_body({"mock": True, "preferred_port": 99999})


def test_build_status(tmp_path):
    p = tmp_path / "settings.json"
    write_setup_stub(path=p)
    st = build_status(listen_port=8080, path=p)
    assert st["setup_complete"] is False
    assert st["listen_port"] == 8080
    assert "127.0.0.1" in st["local_ips"]


def test_save_and_complete_flag(tmp_path):
    p = tmp_path / "settings.json"
    ai = AdventureAI(model="llama3.1:8b", provider="ollama")
    save_settings(ai, mock=True, setup_complete=True, preferred_port=8081, path=p)
    data = load_settings(p)
    assert data["setup_complete"] is True
    assert data["preferred_port"] == 8081
    assert data["mock"] is True


def test_reset_requires_phrase(tmp_path):
    p = tmp_path / "settings.json"
    saves = tmp_path / "saves"
    write_setup_stub(path=p)
    with pytest.raises(ValueError, match="RECONFIGURAR"):
        perform_settings_reset(confirm="no", path=p, saves_base=saves)


def test_reset_wipes_slots(tmp_path):
    p = tmp_path / "settings.json"
    saves = tmp_path / "saves"
    ai = AdventureAI()
    save_slot(ai, 1, name="x", base=saves)
    assert list_slots(base=saves)[0]["occupied"] is True
    save_settings(ai, mock=True, setup_complete=True, path=p)

    out = perform_settings_reset(
        confirm=SETUP_RESET_PHRASE,
        path=p,
        saves_base=saves,
        keep_preferred_port=8080,
    )
    assert out["setup_complete"] is False
    assert out["slots_deleted"] == 1
    assert list_slots(base=saves)[0]["occupied"] is False
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["setup_complete"] is False
    assert data.get("preferred_port") == 8080
