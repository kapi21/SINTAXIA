# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-08 — demo-v1.1 (wizard + memoria trama)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `demo-v1.1` (no mergeado a `main` aún)

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Rama activa de trabajo:** `demo-v1.1`
- **Servidor:** asistente de setup obligatorio + memoria de trama / historial ampliado
- **Aparcado** (`archivo/`, gitignored): presencia_ui, tokenizado_cpc, music_exp, imagen_trabajo, material M4

---

## Hecho (esta tanda)

1. **Setup wizard** en `/ui` (primera instalación + Reconfigurar con wipe total)
2. **Memoria LLM:** historial ~20 mensajes (~10 turnos) alineado guardado/enviado; `plot_summary` al recortar; compactación LLM si crece; persistido en saves
3. Docs: MANUAL + README roadmap + tests `test_setup_wizard` / `test_plot_memory`

---

## Pendiente

1. Probar más en juego real la memoria de trama
2. PR / merge `demo-v1.1` → `main` cuando toque
3. (Opcional) HTTPS PWA  
4. (Largo) TCP / net ASM Z80  
5. (Opcional) subir `imagen/splash2.png` / `splash3.png` si se quieren como arte fuente publicado  

---

## Cómo verificar

- `cd tests` → `python -m pytest`
- Wizard: `SINTAXIA_SETTINGS` temporal + `python server.py --port 18080 --no-browser` → `/ui`
- Memoria: partida larga; hechos viejos deben seguir en coherencia tras >10 turnos

## Riesgos

- Compactar `plot_summary` con LLM añade latencia solo cuando el resumen supera ~900 chars
- Regenerar `TITLE.SCR` con `--force` pisa el arte manual
- `.SCR` sin cabecera AMSDOS → LOAD falla en M4
