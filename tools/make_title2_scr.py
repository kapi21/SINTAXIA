"""Genera client/TITLE2.SCR (MODE 2, 640x200, 2 colores) desde PNG.

El arte se compone a 320x200 (mismo encuadre que MODE 1) y luego cada
pixel se duplica en horizontal -> 640x200. Asi el cartel no queda
'estirado' de mas: en el CPC MODE 2 los pixels son la mitad de anchos
que en MODE 1, y el doble horizontal ocupa el mismo ancho fisico.

Uso (desde la raiz del repo):
  python tools/make_title2_scr.py

Requiere Pillow. En la microSD: T2.SCR junto a aventuramode2.bas (sin carpeta client/).
El generador antepone cabecera AMSDOS para que LOAD\"T2.SCR\",&C000 funcione en la M4.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from amsdos_header import with_amsdos_header

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "server" / "web" / "hero.png"
OUT_SCR = ROOT / "client" / "T2.SCR"
OUT_SCR_ALIAS = ROOT / "client" / "TITLE2.SCR"
OUT_PREVIEW = ROOT / "client" / "title2_preview.png"

# Preview al estilo cliente MODE 2 (negro / verde firmware ~18)
PREVIEW_RGB = [
    (0, 0, 0),
    (0, 200, 0),
]

# Composicion logica (= MODE 1); salida SCR = MODE 2
LW, H = 320, 200
W = LW * 2  # 640
SCR_SIZE = 16384

_BAYER4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]

GLYPHS_5x5: dict[str, list[str]] = {
    "S": ["01110", "10000", "01110", "00001", "01110"],
    "I": ["11111", "00100", "00100", "00100", "11111"],
    "N": ["10001", "11001", "10101", "10011", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100"],
    "A": ["01110", "10001", "11111", "10001", "10001"],
    "X": ["10001", "01010", "00100", "01010", "10001"],
    "P": ["11110", "10001", "11110", "10000", "10000"],
    "U": ["10001", "10001", "10001", "10001", "01110"],
    "L": ["10000", "10000", "10000", "10000", "11111"],
    "E": ["11111", "10000", "11110", "10000", "11111"],
    "C": ["01110", "10001", "10000", "10001", "01110"],
    "O": ["01110", "10001", "10001", "10001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000"],
}


def scr_offset(x: int, y: int) -> int:
    """MODE 2: 8 pixels/byte; mismo entrelazado de scanlines que MODE 1."""
    return ((y & 7) * 0x800) + ((y >> 3) * 80) + (x >> 3)


def pack_mode2(pixels8: list[int]) -> int:
    b = 0
    for i, p in enumerate(pixels8):
        if p:
            b |= 1 << (7 - i)
    return b


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def build_bw_logical(img: Image.Image) -> list[list[int]]:
    """Dither Bayer a 320x200 -> 0/1. Sube un poco el brillo para MODE 2 oscuro."""
    # Autocontraste suave: muchas splashes son muy oscuras y salen casi negras
    from PIL import ImageOps

    img = ImageOps.autocontrast(img.convert("RGB"), cutoff=2)
    pix = img.load()
    rows: list[list[int]] = []
    for y in range(H):
        row = []
        for x in range(LW):
            lum = luminance(pix[x, y])
            # Umbral mas bajo -> mas pixels verdes (cartel mas legible en CRT)
            thr = (_BAYER4[y & 3][x & 3] + 0.5) * (200.0 / 16.0)
            row.append(1 if lum >= thr else 0)
        rows.append(row)
    return rows


def double_horizontal(rows320: list[list[int]]) -> list[list[int]]:
    """Cada pixel MODE1-logico -> 2 pixels MODE2 (aspecto correcto en CRT)."""
    out: list[list[int]] = []
    for y in range(H):
        row = rows320[y]
        out.append([p for p in row for _ in (0, 1)])
    return out


def blit_text(
    rows: list[list[int]],
    text: str,
    x0: int,
    y0: int,
    ink: int,
    scale: int = 1,
    width: int = LW,
) -> None:
    gw = 5 * scale
    gap = max(1, scale)
    x = x0
    for ch in text:
        g = GLYPHS_5x5.get(ch, GLYPHS_5x5[" "])
        for gy, line in enumerate(g):
            for gx, bit in enumerate(line):
                if bit != "1":
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        xx = x + gx * scale + sx
                        yy = y0 + gy * scale + sy
                        if 0 <= xx < width and 0 <= yy < H:
                            rows[yy][xx] = ink
        x += gw + gap


def clear_band(
    rows: list[list[int]], y0: int, y1: int, ink: int = 0, width: int = LW
) -> None:
    for y in range(max(0, y0), min(H, y1)):
        for x in range(width):
            rows[y][x] = ink


def rows_to_scr(rows: list[list[int]]) -> bytes:
    buf = bytearray(SCR_SIZE)
    for y in range(H):
        row = rows[y]
        for xb in range(80):
            x = xb * 8
            buf[scr_offset(x, y)] = pack_mode2(row[x : x + 8])
    return bytes(buf)


def rows_to_preview(rows: list[list[int]]) -> Image.Image:
    """Preview con aspect approx CRT MODE2 (pixels estrechos): escala X/2 visual."""
    # Mostrar a 320x200 para que se vea el encuadre real, no un banner ultraancho
    im = Image.new("RGB", (LW, H))
    px = im.load()
    for y in range(H):
        for x in range(LW):
            # filas MODE2 tienen 640; tomamos el pixel par (bloque duplicado)
            on = rows[y][x * 2]
            px[x, y] = PREVIEW_RGB[1 if on else 0]
    return im


def main() -> None:
    candidates = [
        ROOT / "imagen" / "splash2.png",
        ROOT / "imagen" / "splash3.png",
        ROOT / "imagen" / "splash.png",
        SRC,
    ]
    src_path = next((p for p in candidates if p.is_file()), None)
    if src_path is None:
        raise SystemExit("No existe imagen de origen (imagen/splash*.png o hero.png)")
    print(f"Procesando imagen: {src_path}")
    src = Image.open(src_path).convert("RGB")
    # Mismo encuadre que TITLE.SCR (MODE 1), no estirar a 640
    scaled = src.resize((LW, H), Image.Resampling.LANCZOS)
    rows320 = build_bw_logical(scaled)

    clear_band(rows320, 0, 28, 0)
    clear_band(rows320, H - 18, H, 0)

    title = "SINTAXIA"
    scale = 3
    total_w = len(title) * (5 * scale + scale) - scale
    blit_text(rows320, title, max(0, (LW - total_w) // 2), 6, ink=1, scale=scale)

    foot = "PULSA ESPACIO"
    fw = len(foot) * (5 + 1) - 1
    blit_text(rows320, foot, max(0, (LW - fw) // 2), H - 14, ink=1, scale=1)

    rows = double_horizontal(rows320)
    assert len(rows[0]) == W

    on_count = sum(sum(r) for r in rows)
    print(f"Pixels ON: {on_count}/{W * H} ({100.0 * on_count / (W * H):.1f}%)")

    scr = rows_to_scr(rows)
    out_t2 = with_amsdos_header(scr, "T2.SCR", load_addr=0xC000)
    out_alias = with_amsdos_header(scr, "TITLE2.SCR", load_addr=0xC000)
    OUT_SCR.parent.mkdir(parents=True, exist_ok=True)
    OUT_SCR.write_bytes(out_t2)
    OUT_SCR_ALIAS.write_bytes(out_alias)
    rows_to_preview(rows).save(OUT_PREVIEW)
    print(f"OK {OUT_SCR} ({len(out_t2)} bytes = 128 AMSDOS + {len(scr)} pantalla)")
    print(f"OK alias {OUT_SCR_ALIAS} ({len(out_alias)} bytes)")
    print(f"Preview {OUT_PREVIEW} (mostrado {LW}x{H}, aspecto correcto)")
    print("En la SD: mismo directorio que el .bas — LOAD no usa la ruta client/")


if __name__ == "__main__":
    main()
