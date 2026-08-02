# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-02 (noche)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Hecho (sesión):**
  - Splash `TITLE.SCR` Mode 1 OK en hardware; ping EOF fix; sin paginación; filtro `downloaded`
  - Hasta **12 líneas** de narración (varias filas `T:` + `LN$(12)` en BASIC)
  - Panel: **Generar prompt** / **Prompt por defecto**; abre `/ui` al arrancar (`--no-browser` para no)
  - Generación = **mundo creativo** (LLM) + **reglas fijas** (`prompts/rules_fixed.txt`) → prompt compatible
  - Al generar: también **estado inicial** (L/I/F); al Guardar se aplica y se limpia historial
  - `/intro`: resumen narrativo de arranque (lugar/inventario/atmosfera); CPC lo muestra tras ping / tras `NUEVA`
  - `NUEVA` / `REINICIO`: `/reset` restaura `start_state` del servidor + vuelve a pedir `/intro`
  - Filtro de respuestas con meta en barras (`T:.../S:2/E:0`)
  - Docs: `ESQUEMA_PAQUETE.md`, guía y manual actualizados
- **Pendiente:**
  - Cuota Gemini / pulir I/L/F del Master en partida
  - TCP Z80 (largo)
- **Verificar:**
  - `run_server.bat` → panel automático → Generar prompt → Guardar → CPC `RUN"aventura"` / `NUEVA`
- **Riesgos:** `P$` fija; reiniciar servidor tras cambios Python; SCR overscan no vale para BASIC

---

## Flujo CPC al arrancar

1. Splash `TITLE.SCR` (ESPACIO) o fallback texto  
2. Intro comandos + ping `/ping`  
3. Si OK: **Situacion** vía `/intro` (resumen del mundo actual)  
4. Prompt `>`  

`NUEVA`/`REINICIO` = `/reset` (mundo base del PC) + `/intro` de nuevo.

---

## Panel / generación de mundos

| Botón | Efecto |
|-------|--------|
| Generar prompt | LLM inventa WORLD+STATE; servidor ensambla prompt con `rules_fixed.txt` |
| Prompt por defecto | `master.txt` + estado castillo vacío |
| Guardar | Aplica system + `start_state` (si hay pendiente) |

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

## Endpoints CPC / panel

| Ruta | Uso |
|------|-----|
| `/ping` | Salud |
| `/intro` | Resumen narrativo de arranque |
| `/turn?msg=` | Turno |
| `/reset` | Reinicio al `start_state` |
| `/ui` | Panel (se abre solo al arrancar) |
| `/api/generate_prompt` | Mundo + state |
| `/api/default_prompt` | master + state default |
| `/api/config` | Config (+ `start_state` opcional) |

---

## Protocolo (recordatorio)

```text
T:narracion|en|segmentos   ← solo esto al jugador
S:0-5
E:0|1
I:+obj / L:lugar / F:clave=1   ← solo PC
```

Máx. 12×40; varias filas `T:` si hace falta. Nunca unir con `/`.

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `client/aventura.bas` | Cliente (splash, intro, LN$, NUEVA) |
| `client/TITLE.SCR` | Titulo Mode 1 |
| `server/server.py` | HTTP + locks + browser |
| `server/ai_adventure.py` | LLM, generate world, intro, scrub |
| `server/prompts/rules_fixed.txt` | Reglas T/S/E inmutables |
| `server/prompts/master.txt` | Prompt por defecto |
| `server/web/ui.html` | Panel |
| `docs/ESQUEMA_PAQUETE.md` | Esquema T/S/E/I/L/F |
| `docs/GUIA_JUGADOR.md` / `MANUAL.md` | Docs usuario |

---

## Decisiones

- MODE 1; HTTP; plantilla fija + mundo LLM  
- `start_state` en servidor para resets coherentes  
- No subir `ConvImgCpc.exe`, saves JSON, overscan SCR  
- Reiniciar `server.py` tras cambiar Python  

---

## Proximos pasos

1. Probar Generar → Guardar → CPC intro + NUEVA en hardware  
2. Seguir puliendo narracion I/L/F en partida  
3. (Largo) net ASM  

---

## Notas Windows

`run_server.bat` / `run_server.bat --no-browser`  
Rutas con `@`: comillas / `-LiteralPath`
