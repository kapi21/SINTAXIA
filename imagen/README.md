# imagen/ — arte fuente

PNGs de trabajo / referencia. El splash oficial del CPC se genera así:

```bat
python tools\make_title_scr.py
python tools\make_title2_scr.py
```

(salida: `client/TITLE.SCR` MODE 1, `client/TITLE2.SCR` MODE 2; origen preferido `imagen/splash*.png` o `server/web/hero.png`)

| Fichero | Notas |
|---------|--------|
| `splash.png` / `splash2.png` / `splash3.png` | Candidatos / bocetos |
| `icon.png` | Icono |

Intermedios ConvImgCPC (`.exe`, `.asm`, `.scr`) → `archivo/imagen_trabajo/`.
