# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-02 (sesión noche)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — motor de aventura conversacional con IA para Amstrad CPC + M4 Board
- **Hecho:**
  - Cliente BASIC + servidor multi-LLM + panel `/ui` + saves + guías (base previa)
  - **FIX:** Cuelgue post-ping — el bucle de `PING.TXT` hacía `GOTO 7560` (saltaba el `IF EOF`); corregido a `GOTO 7550` (como `RESP.TXT`)
  - **FIX:** Sin paginación `[ESPACIO para continuar]`; el texto de turno se imprime completo
  - **FIX:** Se filtra/borra el mensaje M4 `downloaded in Xs` (pantalla + líneas del fichero + sufijo en `T$`)
  - **OK en hardware:** splash gráfico `TITLE.SCR` → ESPACIO → intro/ping → prompt `>`
  - Splash: `LOAD"TITLE.SCR",&C000`; si falta el fichero, fallback texto + `Err` visible
  - `client/TITLE.SCR` actual = export **Mode 1 estándar** (ConvImgCPC, ~16 KB + cabecera AMSDOS) — validado en CPC real
  - `tools/make_title_scr.py` prioriza `imagen/splash2.png` → `splash.png` → hero (alternativa sin ConvImg)
- **Pendiente:**
  - Cuota/billing Gemini API (AI Studio ≠ suscripción Gemini Pro chat)
  - Pulir coherencia LLM con I/L/F
  - Cliente TCP Z80 (largo plazo)
- **Cómo verificar:**
  - PC: `run_server.bat` → http://127.0.0.1:8080/ui
  - Regenerar título (Pillow): `python tools/make_title_scr.py`
  - CPC: SD con `aventura.bas` + `TITLE.SCR` (misma carpeta) → `RUN"aventura` → ESPACIO → jugar
- **Riesgos:** `P$` IP fija en BASIC; Gemini free tier puede dar 429 (`limit: 0`); **reiniciar servidor tras cambios Python**; `.bas` ASCII puede necesitar tokenizar; tope texto CPC ~6×40 / 255 chars

---

## Splash / TITLE.SCR (importante)

| Qué | Detalle |
|-----|---------|
| En SD | `TITLE.SCR` junto a `aventura.bas` |
| Válido | Mode **1** estándar (~16384–16512 bytes). Carga `LOAD",&C000` |
| Inválido | SCR **overscan/fullscreen** ConvImg (~32064 bytes, load `&200`) — no usar con BASIC |
| ConvImgCPC | Abrir PNG → **Mode 1** → **sin** Fullscreen/Overscan → Save SCR sin compresión |
| Fallback | Si `LOAD` falla: texto `SINTAXIA` + `(Sin TITLE.SCR Err N)` + Pulsa ESPACIO |
| Local only | `imagen/ConvImgCpc.exe`, `*.scr` overscan, `1.asm` — no subir al repo |

Fuentes de arte en `imagen/`: `splash.png` (en repo), `splash2.png` (local / opcional).

---

## Objetivo

Conectar un **Amstrad CPC real** a un LLM vía **M4 Board (Wi‑Fi)**:

1. Jugador escribe en lenguaje natural en el CPC  
2. Servidor Python en el PC → Ollama / OpenAI / Claude / Gemini / Compatible / mock  
3. Respuesta empaquetada CPC-safe (40 cols, ASCII, CRLF)  
4. BASIC imprime texto + `SOUND`/`ENV`/`ENT` en **AY‑3‑8912**  
5. Estado (inventario, lugar, flags) en el PC; comando `INV` en el CPC  

---

## Red PoC

| Nodo | IP / puerto |
|------|-------------|
| Gateway | `192.168.1.1` |
| PC (servidor) | `192.168.1.4` |
| M4 / CPC | `192.168.1.128` |
| HTTP | **8080** |
| Ollama | `127.0.0.1:11434` |
| Modelo default | `llama3.1:8b` |

Cambiar IP del PC → variable `P$` al inicio de `client/aventura.bas`.

---

## Arquitectura

```text
CPC + M4                         PC
client/aventura.bas              server/server.py :8080
  TITLE.SCR (splash)             web/ui.html + hero.png
  intro + ping                   llm_providers.py (defaults/mapeo)
  INPUT ──HTTP GET /turn──────►  ai_adventure.py → LLM
  |HTTPGET → RESP.TXT            game_state.py (I/L/F)
  parse T:/S:/E:                 protocol.py + cpc_text.py
  BORDER + SOUND AY
  INV / NUEVA / SAVE n / LOAD n / SAVES / AYUDA / QUIT
```

**Proveedores LLM:** `ollama` | `openai` | `claude` | `gemini` | `openai_compat`  
**Transporte:** HTTP (`|HTTPGET`). TCP/ASM = futuro.

### Concurrencia (importante)

`server.py` usa `ThreadingHTTPServer` con **dos locks independientes**:

| Lock | Protege | Duración |
|------|---------|----------|
| `_state_lock` | config, reset, saves, mock, ping — cualquier ruta rápida | milisegundos |
| `_turn_lock` | la llamada al LLM en `ai.turn()` | 5–120 s |

### Endpoints

| Ruta | Uso |
|------|-----|
| `GET /ui` | Panel web |
| `GET /assets/hero.png` | Arte del panel / README |
| `GET /api/saves` | Lista slots 1-3 |
| `POST /api/save` / `POST /api/load` | Slots |
| `GET /ping` | Salud (CPC intro) |
| `GET /turn?msg=` | Turno |
| `GET /reset` | Nueva partida |
| `GET/POST /api/config` | Config LLM |
| `GET /api/status` | mock / ok |
| `POST /api/reset` | Reset desde panel |
| `GET /api/models?...` | Lista modelos por proveedor |

---

## Protocolo

```text
T:linea1|linea2|...
S:2
E:0
```

- Al CPC solo importan **T/S/E** (CRLF). I/L/F solo en PC.  
- Topes: **40** cols, **máx. 6** líneas, cuerpo `T:` ≤ **250**.  
- **S:** 0 neutro · 1 peligro · 2 ambiente · 3 objeto · 4 combate · 5 victoria  

---

## Estructura

```text
M4/
  README.md
  LICENSE
  run_server.bat
  client/
    aventura.bas            # splash, intro, ping, typewriter, AY, comandos
    TITLE.SCR               # Mode 1 estándar (ConvImg o make_title_scr.py)
  tools/
    make_title_scr.py       # PNG → TITLE.SCR 16KB (Pillow)
  server/                   # HTTP + LLM + panel + saves
  imagen/                   # arte fuente; ConvImg local (no exe en git)
  docs/
    SINTAXIA_HANDOFF.md     ← este archivo
    MANUAL.md / GUIA_JUGADOR.md / CARGA.md
```

---

## Cronología (resumen)

1. PoC HTTP + BASIC + AY + panel + multi-LLM  
2. Splash TITLE.SCR + script Pillow  
3. Fixes M4 (URL, LINE INPUT, CRLF, locks, `/api/models`)  
4. **Sesión actual:** fix EOF ping (`GOTO 7550`), quitar paginación, filtrar `downloaded`, splash Mode 1 validado en hardware  

---

## Arranque (siguiente sesión)

### PC
```powershell
cd "C:\@MIS PROYECTOS\M4"
.\run_server.bat
# Panel: http://127.0.0.1:8080/ui
# Regenerar titulo: python tools/make_title_scr.py
```

**Gemini API key:** https://aistudio.google.com/app/apikey (no es la suscripción Gemini Pro del chat).

### CPC
1. Copiar `client/aventura.bas` **y** `client/TITLE.SCR` a la SD (misma carpeta)  
2. `|NETSTAT` → `RUN"aventura` → **ESPACIO** en el titulo  
3. Comandos: `AYUDA`, `NUEVA`, `INV`, `SAVE 1`, `LOAD 1`, `SAVES`, `!`, `D`, `QUIT`  

---

## Decisiones a respetar

- MODE **1** (no MODE 2) salvo decisión explícita  
- Splash = SCR **estándar** Mode 1 para `LOAD",&C000` — nunca overscan ConvImg en el cliente BASIC  
- HTTP, no TCP en el PoC  
- PC reempaqueta siempre (`repack_llm_text`)  
- RSX con variable (`|HTTPGET,@A$`)  
- API keys solo en memoria del panel (no commitear secretos)  
- No subir `archivo/`, `server/saves/*.json`, `ConvImgCpc.exe`, ni `*- copia.png`  
- **Reiniciar** `server.py` tras cualquier cambio Python  
- Dos locks: `_state_lock` (ms) vs `_turn_lock` (s) — no mezclar  
- Tras `|HTTPGET`, bucle de lectura **siempre** vuelve al `IF EOF` (no a `LINE INPUT`)

---

## Próximos pasos sugeridos

1. Mejorar que el LLM use I/L/F de forma fiable  
2. Más atmósfera BASIC (ventanas, música corta)  
3. (Largo) cliente net ASM M4  

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `client/aventura.bas` | Cliente CPC |
| `client/TITLE.SCR` | Pantalla titulo Mode 1 |
| `tools/make_title_scr.py` | Genera TITLE.SCR desde PNG |
| `server/server.py` | HTTP + locks |
| `server/ai_adventure.py` | LLM multi-provider |
| `server/web/ui.html` | Panel |
| `docs/MANUAL.md` / `GUIA_JUGADOR.md` / `CARGA.md` | Docs |
| `LICENSE` | MIT |

---

## Notas Windows

- Rutas con `@`: `-LiteralPath` / comillas  
- Arranque: `run_server.bat` desde la raíz  
- Material hardware en `archivo/` (no Git)  
- ConvImgCPC: herramienta local en `imagen/` (no versionar el `.exe`)  
