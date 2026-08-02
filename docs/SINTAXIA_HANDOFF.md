# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-02 (actualizado tarde)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch / HEAD:** `main` @ `f23d533` (hero en README)

---

## Estado

- **Proyecto:** SINTAXIA — motor de aventura conversacional con IA para Amstrad CPC + M4 Board
- **Hecho:** PoC completo y publicado: cliente BASIC, servidor HTTP, Ollama/API, panel web estilo CPC, inventario/estado, save/load slots 1-3, README con arte hero
- **Pendiente:**
  - Pulir coherencia LLM con flags/lugares
  - Cliente TCP Z80 (largo plazo)
- **Cómo verificar:** `run_server.bat` → http://127.0.0.1:8080/ui → CPC `RUN"aventura`
- **Riesgos:** IP PC hardcodeada en BASIC (`P$`); Ollama en `:11434`; firewall 8080; `.bas` ASCII puede necesitar tokenizar; tope texto CPC ~6×40 / 255 chars

---

## Objetivo

Conectar un **Amstrad CPC real** a un LLM vía **M4 Board (Wi‑Fi)**:

1. Jugador escribe en lenguaje natural en el CPC  
2. Servidor Python en el PC → Ollama / API OpenAI-compatible / mock  
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
  intro + ping /ui ◄───────────  web/ui.html (panel CPC-style)
  INPUT ──HTTP GET /turn──────►  ai_adventure.py → LLM
  |HTTPGET → RESP.TXT            game_state.py (I/L/F)
  parse T:/S:/E:                 protocol.py + cpc_text.py
  BORDER + SOUND AY
  INV / NUEVA / SAVE n / LOAD n / SAVES / AYUDA / QUIT
```

**Transporte:** HTTP (`|HTTPGET`). TCP/ASM = futuro.

### Endpoints

| Ruta | Uso |
|------|-----|
| `GET /ui` | Panel web (estilo CPC + hero.png) |
| `GET /assets/hero.png` | Arte del panel / README |
| `GET /api/saves` | Lista slots 1-3 |
| `POST /api/save` | Guarda slot `{slot, name?}` |
| `POST /api/load` | Carga slot `{slot}` |
| `GET /ping` | Salud (CPC intro) |
| `GET /turn?msg=` | Turno / `inventario` |
| `GET /reset` | Nueva partida |
| `GET/POST /api/config` | Config LLM + estado |
| `GET /api/status` | mock / ok |
| `POST /api/reset` | Reset desde panel |
| `GET /api/models` | Lista modelos Ollama |

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
- Topes: **40** cols, **máx. 6** líneas, cuerpo `T:` ≤ **250** (límite string CPC ~255). Corte → `...`

**S:** 0 neutro · 1 peligro · 2 ambiente · 3 objeto · 4 combate · 5 victoria  

---

## Estructura

```text
M4/
  README.md                 # incluye hero centrado
  run_server.bat
  .gitignore
  client/aventura.bas       # MODE 1, intro, ping, AY, INV/NUEVA
  server/
    server.py
    ai_adventure.py
    game_state.py
    save_game.py            # slots JSON en server/saves/
    protocol.py
    cpc_text.py
    prompts/master.txt
    web/ui.html
    web/hero.png
    saves/.gitkeep          # *.json gitignored
  tests/
  docs/
    CARGA.md
    SINTAXIA_HANDOFF.md     ← este archivo
    superpowers/plans/…     # gitignored
  archivo/                  # local only (docs M4, fotos, carcasas…)
```

Repo público: https://github.com/kapi21/SINTAXIA — layout `client/` + `server/` ya pusheado.

---

## Cronología (resumen)

1. M4 en Wi‑Fi `192.168.1.128`  
2. PoC HTTP mock + BASIC + SOUND  
3. Fix CRLF (`LINE INPUT` CPC)  
4. Ollama + reempaquetado  
5. Repo SINTAXIA; reorg carpetas; panel `/ui` estilo CPC + hero  
6. Topes de texto 6 líneas / 250 chars  
7. Inventario/estado (`INV`, panel, meta I/L/F)  
8. Hero en README GitHub (`f23d533`)  

**Commits recientes:** `671d037` panel/layout · `d14a2c0` estado · `f23d533` README art  

---

## Arranque (siguiente sesión)

### PC
```powershell
cd "C:\@MIS PROYECTOS\M4"
.\run_server.bat
# Panel: http://127.0.0.1:8080/ui
# LAN:   http://192.168.1.4:8080/ui
```

### CPC
1. Copiar `client/aventura.bas` a la SD (tokenizar si hace falta)  
2. `|NETSTAT` → `RUN"aventura`  
3. Comandos: `AYUDA`, `NUEVA`, `INV`, `SAVE 1`, `LOAD 1`, `SAVES`, `QUIT`  

Ver también `docs/MANUAL.md` (manual completo) y `docs/CARGA.md`.

---

## Decisiones a respetar

- MODE **1** (no MODE 2) salvo decisión explícita  
- HTTP, no TCP en el PoC  
- PC reempaqueta siempre (`repack_llm_text`)  
- Sonido: código en PC, tabla AY en BASIC  
- RSX con variable (`|HTTPGET,@A$`)  
- API keys solo en memoria del panel (no commitear secretos)  
- No subir `archivo/` ni `*- copia.png`  

---

## Próximos pasos sugeridos

1. Mejorar que el LLM use I/L/F de forma fiable  
2. Más atmósfera BASIC (ventanas, música corta)  
3. (Largo) cliente net ASM M4  

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `server/server.py` | HTTP CPC + API panel |
| `server/ai_adventure.py` | LLM Ollama/OpenAI + historial |
| `server/game_state.py` | Inventario, lugar, flags |
| `server/save_game.py` | Persistencia slots 1-3 |
| `server/protocol.py` | Paquete T/S/E + topes |
| `server/web/ui.html` | Panel visual CPC |
| `server/web/hero.png` | Arte panel + README |
| `client/aventura.bas` | Cliente real |
| `README.md` | Doc pública con banner |
| `docs/MANUAL.md` | Manual tecnico / instalacion detallada |
| `docs/GUIA_JUGADOR.md` | Guia sencilla para el jugador |
| `docs/CARGA.md` | Carga en hardware |

---

## Notas Windows

- Rutas con `@`: `-LiteralPath` / comillas  
- Arranque: `run_server.bat` desde la raíz  
- Material hardware en `archivo/` (no Git)  
