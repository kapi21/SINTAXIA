# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-05 (tarde — lote cliente 1–4)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Servidor:** estable
- **Hecho (lote alto cliente, 2026-08-05):**
  1. Separador de turno (`STRING$(40,"-")` tras cada respuesta)
  2. Historial 5 comandos (flechas ARR/ABJ; `!` = último)
  3. Confirmación S/N en `QUIT` y `NUEVA`/`REINICIO`
  4. Softkeys f3=`SAVE 1`, f4=`LOAD 1`, f5=`NUEVA` (+ f1/f2 previos)
  - Docs: `GUIA_JUGADOR.md`, `MANUAL.md`, plan marcado hecho
- **Pendiente:**
  - Probar en hardware (copiar `aventura.bas` + `TITLE.SCR` a SD)
  - Cola media del plan: HOST.TXT, paginado turnos, RAPIDO/MUTE, errores RESP…
  - (Largo) TCP/net ASM
- **Verificar en CPC:** historial ↑↓, f3–f5, confirm S/N, separador tras narración
- **Riesgos:** `settings.json` no subir; líneas BASIC ≤32767; HEADER local sin commit

Plan detalle: `docs/superpowers/plans/2026-08-05-client-cpc-mejoras.md`

---

## Flujo CPC al arrancar

1. Splash `TITLE.SCR` + tema intro → ESPACIO (corta sonido)  
2. Pantalla ayuda / comandos / IP `P$` + tono suave → ESPACIO  
3. Ping `/ping`  
4. Si OK: **Situacion** vía `/intro` (MUNDO completo; ESPACIO entre páginas)  
5. Prompt `>` (editor INKEY$)

`NUEVA` / `REINICIO` = `/reset` (`start_state`) + `/intro`.

---

## Panel / IA / persistencia

| Pieza | Detalle |
|-------|---------|
| Proveedores | Ollama, OpenAI, Claude, Gemini, **OpenRouter**, Compatible |
| Guardar (panel) | Aplica config + escribe `server/settings.json` |
| `/intro` | Sin LLM: parsea MUNDO del system prompt |

Esquema T/S/E/I/L/F: `docs/ESQUEMA_PAQUETE.md`

---

## Red PoC

| Nodo | IP / puerto |
|------|-------------|
| PC | `192.168.1.4:8080` |
| M4 | `192.168.1.128` |
| Ollama | `127.0.0.1:11434` |

`P$` en `client/aventura.bas`.

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `client/aventura.bas` | Cliente CPC |
| `client/TITLE.SCR` | Titulo Mode 1 |
| `docs/superpowers/plans/2026-08-05-client-cpc-mejoras.md` | **Plan mañana (cliente)** |
| `docs/GUIA_JUGADOR.md` / `MANUAL.md` | Docs usuario |
| `server/*` | HTTP + LLM (estable) |

---

## Decisiones

- MODE 1; HTTP; sin cabecera gráfica fija en partida  
- Servidor estable → siguientes mejoras = **cliente**  
- No charset / no `G:` por ahora  
- No subir settings con API keys ni restos HEADER  

---

## Proximos pasos

1. Probar lote 1–4 en CPC real (SD)  
2. Cola media del plan si interesa (`HOST.TXT`, paginado turnos, MUTE…)  
3. (Largo) net ASM  

---

## Notas Windows

`run_server.bat` / `run_server.bat --no-browser`  
Rutas con `@`: comillas / `-LiteralPath`
