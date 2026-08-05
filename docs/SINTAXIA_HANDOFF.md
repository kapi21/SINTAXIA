# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-05 (cierre noche)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Servidor:** `?cols=40|80`, SAVE/LOAD con mundo (`system` + `start_state` + `state` + `history`); LOAD solo RAM (no pisa `settings.json`)
- **Clientes CPC:**
  - `sintaxia.bas` — launcher (**1**=MODE1, **2**=MODE2)
  - `aventura.bas` — MODE 1 + `TITLE.SCR`
  - `aventuramode2.bas` — MODE 2 80 cols (CRLF)
- **Softkeys F1–F8:** INV, AYUDA, SAVE/LOAD 1, NUEVA, SONIDO, IP, QUIT
- **QUIT/F8:** «Salir sin guardar?» → pantalla de bienvenida (sin auto-save, sin `CALL 0`)
- **HOST.TXT:** F7 edita IP; se lee al arranque
- **Panel web:** manifest + iconos (`imagen/icon.png` → `server/web/icon-*.png`); “Añadir a inicio” en móvil por HTTP LAN
- **No subir:** `settings.json`, `.cursorrules`, HEADER/splash locales, `music/`, `docs/superpowers/`

---

## Hecho en esta sesión (resumen)

1. Save/load con mundo completo; resume rico al LOAD  
2. Softkeys F1–F8, HOST.TXT, QUIT sin guardar → bienvenida  
3. Launcher `sintaxia.bas`  
4. Panel instalable (manifest + iconos)  
5. Docs: GUIA, MANUAL, CARGA, HANDOFF

---

## Verificar

1. `run_server.bat` reiniciado  
2. SD: `sintaxia.bas` + `aventura.bas` + `aventuramode2.bas` + `TITLE.SCR` (+ `HOST.TXT` opcional)  
3. `RUN"sintaxia` → 1 / 2  
4. F8 → «Salir sin guardar?» → bienvenida  
5. Móvil: `http://IP:8080/ui` → Añadir a pantalla de inicio  

---

## Pendiente (próxima sesión)

- (Opcional) HTTPS para PWA completa  
- Paginado turnos / RAPIDO si sigue en el plan cliente  
- No integrar el `.asm` inventado de `music/gemini-code-*.py` tal cual  
