# SINTAXIA — Handoff de sesión

**Última sesión:** 2026-11-20 — release demo-v1.1 publicada  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main` (sincronizada con origin)

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Release actual:** [demo-v1.1](https://github.com/kapi21/SINTAXIA/releases/tag/demo-v1.1) (*Latest*, `SINTAXIA_Demo_v1.1.zip`); `demo-v1` queda como histórico (su ZIP no incluye `setup_wizard.py`)
- **Servidor:** asistente de setup obligatorio + memoria de trama / historial ampliado
- **Comunidad:** [artículo en AUA (XeNoMoRPH)](https://auamstrad.es/software/sintaxia-una-aventura-conversacional-con-ia/); comentarios piden vídeo y más coherencia
- **Aparcado** (`archivo/`, gitignored): presencia_ui, tokenizado_cpc, music_exp, imagen_trabajo, material M4

---

## Hecho reciente (2026-11-20 — release v1.1)

1. `tools/pack_jugador.ps1` ahora acepta `-Version` (por defecto 1.1) e incluye `setup_wizard.py` (antes faltaba)
2. ZIP generado y probado (60 tests OK, servidor arranca); release `demo-v1.1` publicada en GitHub
3. Borradores: `docs/RELEASE_v1.1.md` y `docs/AUA_ANUNCIO_v1.1.md` (comentario para AUA, con hueco para el vídeo)

## Hecho anterior (2026-08-12)

1. **Setup wizard** en `/ui` (primera instalación + Reconfigurar con wipe total)
2. **Memoria LLM:** historial ~20 mensajes (~10 turnos) alineado guardado/enviado; `plot_summary` al recortar; compactación LLM si crece; persistido en saves
3. Docs: MANUAL + README roadmap + tests `test_setup_wizard` / `test_plot_memory`
4. Enlace al artículo AUA en README (escena Amstrad + créditos) y este handoff; `demo-v1.1` mergeada a `main`

---

## Pendiente / próximos pasos

1. **Grabar vídeo** (1–2 min, CPC real) y publicar el comentario en AUA (`docs/AUA_ANUNCIO_v1.1.md`)
2. **Fase 2 — coherencia dura:** estado estructurado en `game_state.py` (sala, inventario, flags), acciones del LLM validadas por el servidor, estado inyectado en el prompt, test de 30 turnos
3. Fase 3: pantalla de espera con AY, errores claros en cliente, modo demo sin IA (ver [IDEA_CATALOGO_AVENTURAS.md](IDEA_CATALOGO_AVENTURAS.md))
4. Fase 4: partir `server.py` (~800 líneas), test de integración de un turno con `--mock`
5. Higiene: `client/ascii/sintaxia.dsk` (del 07-08, posible desfase con `aventura.bas`), `imagen/` sin versionar, `dist/` al `.gitignore`
6. (Opcional) HTTPS PWA · (Largo) TCP / net ASM Z80

## Cómo verificar

- `cd tests` → `python -m pytest`
- Wizard: `SINTAXIA_SETTINGS` temporal + `python server.py --port 18080 --no-browser` → `/ui`
- Memoria: partida larga; hechos viejos deben seguir en coherencia tras >10 turnos

## Riesgos

- Compactar `plot_summary` con LLM añade latencia solo cuando el resumen supera ~900 chars
- Regenerar `TITLE.SCR` con `--force` pisa el arte manual
- `.SCR` sin cabecera AMSDOS → LOAD falla en M4
