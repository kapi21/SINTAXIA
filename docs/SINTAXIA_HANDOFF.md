# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-03 (cierre noche)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Hecho (sesión 2026-08-03):**
  - Sin cabecera fija en juego (experimento HEADER descartado; quedan ficheros locales opcionales sin uso)
  - `/intro` = bloque **MUNDO** completo (premisa sin truncar; `CPC_INTRO_MAX_LINES=60`; paginado ESPACIO ~18 líneas en CPC)
  - Filtro de líneas vacías (servidor + cliente); reglas de mayúsculas/puntuación/gramática en `rules_fixed.txt`
  - Wipe M4 `downloaded in…` (filas 24–25); spinner `/-\|` en “Pensando”
  - Bienvenida reordenada: TITLE → ayuda → ESPACIO → ping → Situación → `>`
  - Jingle AY corto en TITLE + tono suave en espera de ayuda; silencio al pulsar ESPACIO
  - Fix Overflow al cargar `.bas`: no usar números de línea >32767 (p. ej. `72485`)
- **Pendiente:**
  - Pulir I/L/F del Master en partida
  - (Largo) TCP/net ASM Z80
- **Verificar:**
  - Copiar `client/aventura.bas` (+ `TITLE.SCR`) a la SD; reiniciar servidor Python
  - Arranque: jingle TITLE → ayuda → ESPACIO → ping → Situación completa (paginada si hace falta)
- **Riesgos:**
  - `server/settings.json` con API key en claro; **no** subir a Git
  - En CPC, números de línea BASIC ≤32767 de forma segura al editar ASCII

---

## Flujo CPC al arrancar

1. Splash `TITLE.SCR` + jingle → ESPACIO (corta sonido)  
2. Pantalla ayuda / comandos / IP `P$` + tono suave → ESPACIO  
3. Ping `/ping`  
4. Si OK: **Situacion** vía `/intro` (MUNDO completo; ESPACIO entre páginas)  
5. Prompt `>`

`NUEVA` / `REINICIO` = `/reset` (`start_state`) + `/intro`.

---

## Panel / IA / persistencia

| Pieza | Detalle |
|-------|---------|
| Proveedores | Ollama, OpenAI, Claude, Gemini, **OpenRouter**, Compatible |
| OpenRouter | Base `https://openrouter.ai/api/v1`; modelo tipico `openrouter/auto` |
| Guardar (panel) | Aplica config + escribe `server/settings.json` |
| Cierre servidor | Vuelve a escribir settings (`atexit` / Ctrl+C) |
| Arranque | Carga settings; flags `--provider`/`--model`/`--api-key`/`--mock` pisan esa sesión |
| Generar prompt | WORLD+STATE; ensambla con `rules_fixed.txt` |
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

## Endpoints

| Ruta | Uso |
|------|-----|
| `/ping` | Salud |
| `/intro` | Resumen MUNDO (completo, sin LLM) |
| `/turn?msg=` | Turno |
| `/reset` | Reinicio al `start_state` |
| `/ui` | Panel |
| `/api/config` | Config (+ persistencia) |
| `/api/generate_prompt` | Mundo + state |
| `/api/default_prompt` | master + state default |
| `/api/models` | Lista modelos del proveedor |

---

## Protocolo (recordatorio)

```text
T:narracion|en|segmentos   ← solo esto al jugador
S:0-5
E:0|1
I:+obj / L:lugar / F:clave=1   ← solo PC
```

Máx. 12×40 en turnos; `/intro` puede enviar más líneas `T:` (cliente paginado). Nunca unir con `/`.

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `client/aventura.bas` | Cliente CPC |
| `client/TITLE.SCR` | Titulo Mode 1 |
| `server/server.py` | HTTP, browser, carga/guarda settings |
| `server/settings_store.py` | Lectura/escritura `settings.json` |
| `server/settings.json` | **Local** (gitignored; API keys) |
| `server/llm_providers.py` | Defaults + OpenRouter headers |
| `server/ai_adventure.py` | LLM, intro MUNDO, generate, scrub |
| `server/protocol.py` | Empaquetado T/S/E; intro sin ellipsis agresivo |
| `server/prompts/rules_fixed.txt` | Reglas T/S/E + gramatica |
| `server/web/ui.html` | Panel |
| `tests/test_mundo_intro.py` | Tests intro MUNDO |
| `docs/ESQUEMA_PAQUETE.md` | Esquema paquete |
| `docs/GUIA_JUGADOR.md` / `MANUAL.md` | Docs usuario |

**Local sin uso en juego (no hace falta en SD):** `HEADER.SCR`, `tools/make_header_scr.py`, previews de header, `imagen/splash2.png`.

---

## Decisiones

- MODE 1; HTTP; plantilla fija + mundo LLM  
- OpenRouter como proveedor de primera clase  
- Settings locales con API key; no subir a GitHub  
- Sin cabecera gráfica fija en partida (pantalla completa de texto)  
- Intro = datos del MUNDO, no llamada LLM  
- No subir `ConvImgCpc.exe`, saves JSON, overscan SCR  

---

## Proximos pasos

1. Probar jingle + intro paginada en hardware real tras copiar `.bas`  
2. Seguir puliendo narracion I/L/F  
3. (Largo) net ASM  

---

## Notas Windows

`run_server.bat` / `run_server.bat --no-browser`  
`run_server.bat --provider openrouter --api-key …`  
Rutas con `@`: comillas / `-LiteralPath`
