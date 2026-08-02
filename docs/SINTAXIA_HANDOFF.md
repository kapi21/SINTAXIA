# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-02 (tarde / cierre sesión)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — motor de aventura conversacional con IA para Amstrad CPC + M4 Board
- **Hecho:**
  - Cliente BASIC: splash `TITLE.SCR` (espacio) + intro/ping + AY + INV/SAVE/LOAD
  - Servidor HTTP + panel `/ui` (estilo CPC, tooltips solo en `?`)
  - LLM multi-proveedor: **Ollama, OpenAI, Claude, Gemini, Compatible**
  - Inventario/estado, slots save 1–3, guías `MANUAL` + `GUIA_JUGADOR`
- **Pendiente:**
  - Probar splash en CPC real (copiar `TITLE.SCR` + `aventura.bas` a la SD)
  - Cuota/billing Gemini API (AI Studio ≠ suscripción Gemini Pro chat)
  - Pulir coherencia LLM con I/L/F
  - Cliente TCP Z80 (largo plazo)
- **Cómo verificar:**
  - PC: `run_server.bat` → http://127.0.0.1:8080/ui
  - Regenerar título: `python tools/make_title_scr.py`
  - CPC: SD con `aventura.bas` + `TITLE.SCR` → `RUN"aventura` → ESPACIO
- **Riesgos:** `P$` IP fija en BASIC; Gemini free tier puede dar 429 (`limit: 0`); reiniciar servidor tras cambios Python; `.bas` ASCII puede necesitar tokenizar; tope texto CPC ~6×40 / 255 chars

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

### Endpoints

| Ruta | Uso |
|------|-----|
| `GET /ui` | Panel web (estilo CPC + hero.png + tooltips `?`) |
| `GET /assets/hero.png` | Arte del panel / README |
| `GET /api/saves` | Lista slots 1-3 |
| `POST /api/save` | Guarda slot `{slot, name?}` |
| `POST /api/load` | Carga slot `{slot}` |
| `GET /ping` | Salud (CPC intro) |
| `GET /turn?msg=` | Turno / `inventario` |
| `GET /reset` | Nueva partida |
| `GET/POST /api/config` | Config LLM + estado (`provider`, `api_base`, key en memoria) |
| `GET /api/status` | mock / ok |
| `POST /api/reset` | Reset desde panel |
| `GET /api/models` | Lista modelos Ollama |

CLI: `python server.py --provider gemini --api-key ... --api-base ...`

---

## Protocolo

```text
T:linea1|linea2|...
S:2
E:0
I:+antorcha          (opcional, solo PC)
L:pasillo norte      (opcional)
F:puerta_abierta=1   (opcional)
```

- Al CPC solo importan **T/S/E** (CRLF).  
- **I/L/F** los consume `game_state.py` y se quitan antes del display CPC.  
- Topes: **40** cols, **máx. 6** líneas, cuerpo `T:` ≤ **250**. Corte → `...`

**S:** 0 neutro · 1 peligro · 2 ambiente · 3 objeto · 4 combate · 5 victoria  

---

## Estructura

```text
M4/
  README.md
  run_server.bat
  .gitignore
  client/
    aventura.bas            # MODE 1, splash, intro, ping, AY, comandos
    TITLE.SCR               # dump pantalla titulo (16 KB)
  tools/
    make_title_scr.py       # hero.png → TITLE.SCR (+ preview local)
  server/
    server.py
    ai_adventure.py
    llm_providers.py        # defaults + mapeo Claude/Gemini
    game_state.py
    save_game.py
    protocol.py
    cpc_text.py
    prompts/master.txt
    web/ui.html
    web/hero.png
    saves/.gitkeep
  tests/
    test_llm_providers.py
    …
  docs/
    CARGA.md
    MANUAL.md
    GUIA_JUGADOR.md
    SINTAXIA_HANDOFF.md     ← este archivo
  archivo/                  # local only
```

---

## Cronología (resumen)

1. M4 en Wi‑Fi + PoC HTTP mock + BASIC + SOUND + fix CRLF  
2. Ollama + panel `/ui` + hero + inventario/saves  
3. Guías jugador + manual técnico  
4. Multi-proveedor LLM (OpenAI / Claude / Gemini / Compatible) + tooltips UI  
5. Splash CPC `TITLE.SCR` desde hero + script `make_title_scr.py`  

---

## Arranque (siguiente sesión)

### PC
```powershell
cd "C:\@MIS PROYECTOS\M4"
.\run_server.bat
# Panel: http://127.0.0.1:8080/ui
# Regenerar titulo: python tools/make_title_scr.py
```

**Gemini API key:** https://aistudio.google.com/app/apikey (no es la suscripción Gemini Pro del chat). Facturación del proyecto Cloud si sale 429 `limit: 0`.

### CPC
1. Copiar `client/aventura.bas` **y** `client/TITLE.SCR` a la SD  
2. `|NETSTAT` → `RUN"aventura` → **ESPACIO** en el titulo  
3. Comandos: `AYUDA`, `NUEVA`, `INV`, `SAVE 1`, `LOAD 1`, `SAVES`, `QUIT`  

Ver `docs/MANUAL.md`, `docs/GUIA_JUGADOR.md`, `docs/CARGA.md`.

---

## Decisiones a respetar

- MODE **1** (no MODE 2) salvo decisión explícita  
- HTTP, no TCP en el PoC  
- PC reempaqueta siempre (`repack_llm_text`)  
- Sonido: código en PC, tabla AY en BASIC  
- RSX con variable (`|HTTPGET,@A$`)  
- API keys solo en memoria del panel (no commitear secretos)  
- No subir `archivo/`, `server/saves/*.json`, ni `*- copia.png`  
- Tras cambiar Python: **reiniciar** `server.py` (el HTML `/ui` se lee fresco del disco)

---

## Próximos pasos sugeridos

1. Validar splash + partida en hardware real  
2. Mejorar que el LLM use I/L/F de forma fiable  
3. Más atmósfera BASIC (ventanas, música corta)  
4. (Largo) cliente net ASM M4  

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `server/server.py` | HTTP CPC + API panel + CLI providers |
| `server/ai_adventure.py` | LLM multi-provider + historial |
| `server/llm_providers.py` | Defaults, URLs, mapeo Claude/Gemini |
| `server/game_state.py` | Inventario, lugar, flags |
| `server/save_game.py` | Persistencia slots 1-3 |
| `server/protocol.py` | Paquete T/S/E + topes |
| `server/web/ui.html` | Panel visual CPC |
| `server/web/hero.png` | Arte panel + fuente del splash |
| `client/aventura.bas` | Cliente real |
| `client/TITLE.SCR` | Pantalla titulo MODE 1 |
| `tools/make_title_scr.py` | Genera TITLE.SCR |
| `docs/MANUAL.md` | Manual tecnico |
| `docs/GUIA_JUGADOR.md` | Guia sencilla |
| `docs/CARGA.md` | Carga en hardware |

---

## Notas Windows

- Rutas con `@`: `-LiteralPath` / comillas  
- Arranque: `run_server.bat` desde la raíz  
- Material hardware en `archivo/` (no Git)  
