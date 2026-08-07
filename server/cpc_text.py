"""Normalizacion de texto para Amstrad CPC (ROM / MODE 1)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

# Sustituciones explicitas antes de strip de acentos (escapes para encoding Windows)
_REPLACEMENTS = {
    "\u00f1": "n",  # n
    "\u00d1": "N",  # N
    "\u00e7": "c",
    "\u00c7": "C",
    "\u00bf": "?",
    "\u00a1": "!",
    "\u00ab": '"',
    "\u00bb": '"',
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u20ac": "E",
    "\u00b0": "o",
    # Puntuacion tipografica / fullwidth que el LLM mete a menudo
    "\uff0c": ",",  # ，
    "\uff0e": ".",  # ．
    "\u3002": ".",  # 。
    "\uff01": "!",  # ！
    "\uff1f": "?",  # ？
    "\uff1b": ";",  # ；
    "\uff1a": ":",  # ：
    "\u00b7": ".",  # ·
    "\u2022": "-",  # •
    "\u201a": ",",  # ‚
    "\u2032": "'",
    "\u2033": '"',
}

_CPC_OK = re.compile(r"[^ -~]")
_SENTENCE_END = frozenset(".!?;:")


def normalize_cpc(text: str) -> str:
    """Quita tildes/especiales y deja solo ASCII printable CPC-safe."""
    if not text:
        return ""
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    decomposed = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    cleaned = _CPC_OK.sub("", without_marks)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n+", " ", cleaned)
    return cleaned.strip()


def join_narrative_segments(parts: Iterable[str]) -> str:
    """Une segmentos T: restaurando '.' si el modelo uso '|' como fin de frase.

    Continuaciones en minuscula (wrap a mitad de frase) se unen con espacio.
    Si el siguiente segmento empieza en mayuscula y el anterior no termina
    en puntuacion, se inserta '. '.
    """
    result = ""
    for raw in parts:
        p = normalize_cpc(str(raw)).strip() if raw is not None else ""
        if not p:
            continue
        if not result:
            result = p
            continue
        prev = result[-1]
        if prev in _SENTENCE_END:
            result += " " + p
        elif p[0].isupper():
            result += ". " + p
        else:
            result += " " + p
    return result


def wrap_lines(text: str, width: int = 40, max_lines: int = 8) -> list[str]:
    """Normaliza y parte en lineas de como maximo `width` caracteres."""
    text = normalize_cpc(text)
    if not text:
        return []

    words = text.split(" ")
    lines: list[str] = []
    current = ""

    for word in words:
        if not word:
            continue
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""
                if len(lines) >= max_lines:
                    return lines
            lines.append(word[:width])
            word = word[width:]
            if len(lines) >= max_lines:
                return lines
        if not word:
            continue
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                return lines

    if current and len(lines) < max_lines:
        lines.append(current)

    return lines[:max_lines]
