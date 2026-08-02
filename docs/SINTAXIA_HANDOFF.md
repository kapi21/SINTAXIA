# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-02 (noche, late)  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  
**Branch:** `main`

---

## Estado

- **Proyecto:** SINTAXIA — aventura conversacional IA para Amstrad CPC + M4 Board
- **Hecho (sesión reciente):**
  - Proveedor **OpenRouter** (opción propia en panel/CLI; API OpenAI-compat; default `openrouter/auto`)
  - Headers de atribución OpenRouter (`HTTP-Referer` + `X-OpenRouter-Title`)
  - Fix: `content: null` de OpenRouter ya no tumba el hilo HTTP (`extract_openai_text` + catch en `turn`)
  - **Persistencia** de ajustes en `server/settings.json` (gitignored): provider, model, urls, api_key, temperature, mock, system, start_state
  - Se escribe al **Guardar** del panel y al **cerrar** el servidor; se carga al arrancar (CLI puede pisar)
  - Docs: handoff, guía, manual al día
- **Hecho (antes, sigue vigente):**
  - Splash `TITLE.SCR` Mode 1; ping EOF; sin paginación; hasta 12 líneas `T:`
  - Generar prompt = WORLD LLM + `rules_fixed.txt`; `/intro`; `NUEVA`/`REINICIO` + `start_state`
- **Pendiente:**
  - Pulir I/L/F del Master en partida
  - TCP Z80 (largo)
- **Verificar:**
  - Configurar OpenRouter → Guardar → cerrar servidor → reabrir → debe cargar settings
  - Turno de prueba / CPC con OpenRouter
- **Riesgos:**
  - `settings.json` tiene la API key en claro (solo local; no subir a Git)
  - No loguear URLs con `api_key=` en claro si se puede evitar; rotar keys si se filtran
  - Reiniciar servidor tras cambios Python

---

## Flujo CPC al arrancar

1. Splash `TITLE.SCR` (ESPACIO) o fallback texto  
2. Intro comandos + ping `/ping`  
3. Si OK: **Situacion** vía `/intro`  
4. Prompt `>`  

`NUEVA`/`REINICIO` = `/reset` (`start_state`) + `/intro`.

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
| `/intro` | Resumen narrativo |
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

Máx. 12×40; varias filas `T:` si hace falta. Nunca unir con `/`.

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
| `server/ai_adventure.py` | LLM, intro, generate, scrub |
| `server/prompts/rules_fixed.txt` | Reglas T/S/E |
| `server/web/ui.html` | Panel |
| `docs/ESQUEMA_PAQUETE.md` | Esquema paquete |
| `docs/GUIA_JUGADOR.md` / `MANUAL.md` | Docs usuario |

---

## Decisiones

- MODE 1; HTTP; plantilla fija + mundo LLM  
- OpenRouter como proveedor de primera clase (no solo Compatible)  
- Settings locales con API key; no subir a GitHub  
- No subir `ConvImgCpc.exe`, saves JSON, overscan SCR  

---

## Proximos pasos

1. Probar persistencia OpenRouter en hardware real  
2. Seguir puliendo narracion I/L/F  
3. (Largo) net ASM  

---

## Notas Windows

`run_server.bat` / `run_server.bat --no-browser`  
`run_server.bat --provider openrouter --api-key …`  
Rutas con `@`: comillas / `-LiteralPath`
