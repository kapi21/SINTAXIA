# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-07 (noche) — docs + push; README GitHub pendiente  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Cliente:** ASCII en `client/*.bas` (+ `client/ascii/` sincronizado)
- **Titulos SD (misma carpeta que el .bas, sin ruta `client/`):**
  - `TITLE.SCR` — **manual del usuario** (no regenerar / no pisar; `make_title_scr.py` escribe `TITLE_gen.SCR` salvo `--force`)
  - `T2.SCR` / `TITLE2.SCR` — MODE 2 con **cabecera AMSDOS** (16512 bytes); generado por `tools/make_title2_scr.py`
- **UX reciente:** “Iniciando la aventura…”, avisos del launcher, AYUDA sin CLS ni pausa ESPACIO
- **Servidor:** estable
- **Aparcado** (`archivo/`, gitignored): presencia_ui, tokenizado_cpc, music_exp, imagen_trabajo, material M4

---

## Hecho (esta tanda)

1. Limpieza: tokenizado/music/herramientas ConvImg → `archivo/` (sin borrar)  
2. MODE 2: splash `T2.SCR` + fallback Dinamic; AMSDOS header (clave para LOAD en M4)  
3. Mensajes de carga; AYUDA no borra pantalla  
4. `ver_title2.bas` para probar titulo MODE 2  
5. Docs: GUIA + MANUAL + este HANDOFF  

---

## Pendiente

1. (Opcional) HTTPS PWA  
2. (Largo) TCP / net ASM Z80  
3. Retomar solo a proposito: `archivo/tokenizado_cpc/` o `archivo/presencia_ui/`  
4. (Opcional) subir `imagen/splash2.png` / `splash3.png` al repo si se quieren como arte fuente publicado  

---

## SD — estructura correcta

```text
sintaxia.bas
aventura.bas
aventuramode2.bas
TITLE.SCR          ← MODE 1 (usuario)
T2.SCR             ← MODE 2 (AMSDOS)
TITLE2.SCR         ← opcional, mismo contenido que T2
ver_title2.bas     ← opcional
HOST.TXT           ← opcional IP:puerto
```

`LOAD` en BASIC: `LOAD"T2.SCR",&C000` — **nunca** `client/...`.

---

## Cómo verificar

- `RUN"sintaxia` → 1/2 → titulo → juego  
- `RUN"ver_title2` → debe mostrar grafico MODE 2  
- AYUDA: texto previo visible; lista completa sin “Pulsa ESPACIO” intermedio  

## Riesgos

- Regenerar `TITLE.SCR` con `--force` pisa el arte manual del usuario  
- `.SCR` sin cabecera AMSDOS → LOAD falla en M4 (parece “no esta”)  
- `archivo/` no se publica (gitignore)  
