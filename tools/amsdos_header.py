"""Cabecera AMSDOS (128 bytes) para que LOAD\"fichero\",&addr funcione en CPC/M4.

Sin cabecera, AMSDOS trata el fichero como ASCII y LOAD falla (parece
'file not found' / error de tipo). La carpeta client/ del PC NO va en el LOAD:
en la SD el nombre es solo T2.SCR / TITLE.SCR junto al .bas.
"""

from __future__ import annotations


def amsdos_header(
    filename: str,
    load_addr: int = 0xC000,
    length: int = 16384,
    file_type: int = 0x02,
) -> bytes:
    """Genera cabecera AMSDOS. filename ej. 'T2.SCR' o 'TITLE.SCR'."""
    name = filename.replace("\\", "/").split("/")[-1].upper()
    if "." in name:
        stem, ext = name.rsplit(".", 1)
    else:
        stem, ext = name, ""
    stem = (stem + "        ")[:8]
    ext = (ext + "   ")[:3]

    h = bytearray(128)
    h[0] = 0
    h[1:9] = stem.encode("ascii")
    h[9:12] = ext.encode("ascii")
    h[18] = file_type & 0xFF
    h[21] = load_addr & 0xFF
    h[22] = (load_addr >> 8) & 0xFF
    h[24] = length & 0xFF
    h[25] = (length >> 8) & 0xFF
    h[26] = load_addr & 0xFF
    h[27] = (load_addr >> 8) & 0xFF
    h[64] = length & 0xFF
    h[65] = (length >> 8) & 0xFF
    h[66] = (length >> 16) & 0xFF
    checksum = sum(h[0:67]) & 0xFFFF
    h[67] = checksum & 0xFF
    h[68] = (checksum >> 8) & 0xFF
    return bytes(h)


def with_amsdos_header(data: bytes, filename: str, load_addr: int = 0xC000) -> bytes:
    return amsdos_header(filename, load_addr=load_addr, length=len(data)) + data
