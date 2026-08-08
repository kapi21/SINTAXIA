"""Tests memoria de trama / historial largo."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from ai_adventure import (
    MAX_HISTORY_MESSAGES,
    AdventureAI,
    fold_plot_summary,
    plot_summary_for_prompt,
)
from save_game import load_slot, save_slot


def test_fold_plot_summary_keeps_facts():
    dropped = [
        {"role": "user", "content": "hablo con el guardia"},
        {"role": "assistant", "content": "El guardia te da la llave oxida."},
    ]
    out = fold_plot_summary("", dropped, max_chars=400)
    assert "guardia" in out.lower()
    assert "llave" in out.lower()
    assert "J:" in out and "N:" in out


def test_fold_plot_summary_truncates():
    big = "x" * 500
    dropped = [{"role": "assistant", "content": big}]
    out = fold_plot_summary("prefijo antiguo", dropped, max_chars=80)
    assert len(out) <= 80


def test_plot_summary_for_prompt_empty():
    assert plot_summary_for_prompt("") == ""
    assert plot_summary_for_prompt("  ") == ""
    block = plot_summary_for_prompt("Abriste la puerta norte.")
    assert "MEMORIA DE TRAMA" in block
    assert "puerta norte" in block.lower()


def test_messages_include_full_history_window_and_plot():
    ai = AdventureAI()
    ai.max_history = 6
    ai.plot_summary = "El rey te encargo recuperar el amuleto."
    for i in range(10):
        ai.history.append({"role": "user", "content": f"accion {i}"})
        ai.history.append({"role": "assistant", "content": f"resultado {i}"})
    # Simula trim como en turn()
    ai._trim_history()
    assert len(ai.history) == 6
    assert "amuleto" in ai.plot_summary.lower() or "accion" in ai.plot_summary.lower()

    msgs = ai._messages("miro alrededor", width=40)
    assert msgs[0]["role"] == "system"
    assert "MEMORIA DE TRAMA" in msgs[0]["content"]
    # system + hasta 6 history + user actual
    assert len(msgs) == 1 + 6 + 1
    assert msgs[-1]["content"] == "miro alrededor"


def test_default_max_history_is_raised():
    ai = AdventureAI()
    assert ai.max_history == MAX_HISTORY_MESSAGES
    assert ai.max_history >= 20


def test_save_load_preserves_plot_summary(tmp_path):
    ai = AdventureAI()
    ai.plot_summary = "Conociste a Mira en la taberna. Te dio un mapa."
    ai.history = [
        {"role": "user", "content": "miro el mapa"},
        {"role": "assistant", "content": "Marca una cueva al este."},
    ]
    save_slot(ai, 1, name="mem", base=tmp_path)
    ai2 = AdventureAI()
    load_slot(ai2, 1, base=tmp_path)
    assert "mira" in ai2.plot_summary.lower()
    assert "mapa" in ai2.plot_summary.lower()


def test_reset_clears_plot():
    ai = AdventureAI()
    ai.plot_summary = "hecho viejo"
    ai.history = [{"role": "user", "content": "x"}]
    ai.reset()
    assert ai.plot_summary == ""
    assert ai.history == []
