# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-05 (noche — MODE2 + mute + cols + push)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Servidor:** estable; `?cols=40|80` + reflow denso
- **Clientes:**
  - `aventura.bas` — MODE 1 (oficial)
  - `aventuramode2.bas` — MODE 2 80 cols (CRLF)
- **Hecho:** MUTE/AUDIO/f6; NUEVA sin Lugar/Llevas; borde negro fijo; viñetas off; docs MODE2
- **Pendiente:** HOST.TXT, paginado turnos, RAPIDO; (largo) TCP/net ASM
- **No subir:** `settings.json`, `.cursorrules`, HEADER/splash locales

Plan: `docs/superpowers/plans/2026-08-05-client-cpc-mejoras.md` (gitignored)

---

## Verificar

1. Reiniciar `run_server.bat`
2. SD: ambos `.bas` + `TITLE.SCR`
3. `RUN"aventura` y `RUN"aventuramode2`
4. MODE2: texto ancho; F5 → intro directa; `MUTE`/`AUDIO`
