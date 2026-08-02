"""Genera client/TITLE.SCR (MODE 1) desde server/web/hero.png.

Uso (desde la raiz del repo):
  python tools/make_title_scr.py

Requiere Pillow.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "server" / "web" / "hero.png"
OUT_SCR = ROOT / "client" / "TITLE.SCR"
OUT_PREVIEW = ROOT / "client" / "title_preview.png"

# Recorte: puerta + heroe (el hero incluye UI; luego se limpian franjas)
CROP = (760, 80, 1480, 940)  # left, top, right, bottom

# Paleta del cliente (aprox. INK 0,1,2,3 del aventura.bas)
PALETTE_RGB = [
    (0, 0, 0),
    (255, 255, 255),
    (0, 255, 255),
    (255, 128, 0),
]

W, H = 320, 200

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


def nearest_ink(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    best, best_d = 0, 1e18
    for i, (pr, pg, pb) in enumerate(PALETTE_RGB):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_d:
            best, best_d = i, d
    return best


def pack_mode1(p0: int, p1: int, p2: int, p3: int) -> int:
    b = 0
    for i, p in enumerate((p0, p1, p2, p3)):
        if p & 1:
            b |= 1 << (7 - i)
        if p & 2:
            b |= 1 << (3 - i)
    return b


def scr_offset(x: int, y: int) -> int:
    return ((y & 7) * 0x800) + ((y >> 3) * 80) + (x >> 2)


def build_indexed(img: Image.Image) -> list[list[int]]:
    pix = img.convert("RGB").load()
    return [[nearest_ink(pix[x, y]) for x in range(W)] for y in range(H)]


def blit_text(
    rows: list[list[int]],
    text: str,
    x0: int,
    y0: int,
    ink: int,
    scale: int = 1,
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
                        if 0 <= xx < W and 0 <= yy < H:
                            rows[yy][xx] = ink
        x += gw + gap


def rows_to_scr(rows: list[list[int]]) -> bytes:
    buf = bytearray(16384)
    for y in range(H):
        row = rows[y]
        for xb in range(80):
            x = xb * 4
            buf[scr_offset(x, y)] = pack_mode1(row[x], row[x + 1], row[x + 2], row[x + 3])
    return bytes(buf)


def rows_to_preview(rows: list[list[int]]) -> Image.Image:
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = PALETTE_RGB[rows[y][x]]
    return im


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"No existe {SRC}")
    src = Image.open(SRC).convert("RGB")
    crop = src.crop(CROP)
    fitted = Image.new("RGB", (W, H), PALETTE_RGB[0])
    body_h = 184
    scaled = crop.resize((W, body_h), Image.Resampling.NEAREST)
    fitted.paste(scaled, (0, 0))
    # Tapar restos de texto/UI del arte original (citas y menu)
    dr = ImageDraw.Draw(fitted)
    dr.rectangle((210, 8, 319, 78), fill=PALETTE_RGB[0])  # citas arriba-derecha
    dr.rectangle((235, 130, 319, 183), fill=PALETTE_RGB[0])  # menu abajo-derecha
    rows = build_indexed(fitted)
    title = "SINTAXIA"
    scale = 3
    total_w = len(title) * (5 * scale + scale) - scale
    blit_text(rows, title, max(0, (W - total_w) // 2), 6, ink=3, scale=scale)
    for y in range(H - 16, H):
        for x in range(W):
            rows[y][x] = 0
    foot = "PULSA ESPACIO"
    fw = len(foot) * 6 - 1
    blit_text(rows, foot, max(0, (W - fw) // 2), H - 14, ink=1, scale=1)
    scr = rows_to_scr(rows)
    OUT_SCR.parent.mkdir(parents=True, exist_ok=True)
    OUT_SCR.write_bytes(scr)
    rows_to_preview(rows).save(OUT_PREVIEW)
    print(f"OK {OUT_SCR} ({len(scr)} bytes)")
    print(f"Preview {OUT_PREVIEW}")


if __name__ == "__main__":
    main()
