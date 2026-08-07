# client/ — ficheros para la microSD

Fuente de trabajo (ultima version). Copia a la SD:

| Fichero | Uso |
|---------|-----|
| `sintaxia.bas` | Launcher MODE 1 / 2 |
| `aventura.bas` | Juego MODE 1 |
| `aventuramode2.bas` | Juego MODE 2 |
| `TITLE.SCR` | Titulo grafico MODE 1 (**hecho a mano / oficial**; no regenerar a ciegas) |
| `T2.SCR` | Titulo grafico MODE 2 (**con cabecera AMSDOS**; misma carpeta que el .bas) |
| `TITLE2.SCR` | Alias del mismo titulo MODE 2 |
| `ver_title2.bas` | Ver solo el titulo MODE 2 (prueba) |

**Importante:** en el CPC el `LOAD` es `LOAD"T2.SCR",&C000` — no existe ruta `client/`. Esa carpeta es solo en el PC.

Respaldo ASCII (misma copia): carpeta `ascii/`.

Regenerar titulos en el PC:

```bat
python tools\make_title_scr.py
python tools\make_title2_scr.py
```
