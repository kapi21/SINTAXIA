# SINTAXIA — Handoff de sesión

**Fecha:** 2026-08-02  
**Workspace local:** `C:\@MIS PROYECTOS\M4`  
**Repo GitHub:** https://github.com/kapi21/SINTAXIA  

---

## Estado

- **Proyecto:** SINTAXIA — motor de aventura conversacional con IA para Amstrad CPC + M4 Board
- **Hecho:** PoC jugable punta a punta (mock → Ollama), cliente BASIC con AY, protocolo `T:/S:/E:`, repo ordenado y publicado
## Pendiente (roadmap)
- ~~Ambiente visual CPC (intro + ping + paleta + borde)~~ → `client/aventura.bas`
- ~~Sonidos AY ricos (ENV/ENT)~~ → envolventes 1-5 + ruido en combate
- ~~Panel web PC (Ollama vs API)~~ → `http://127.0.0.1:8080/ui`
- ~~Push estructura `client/`/`server/` a GitHub~~ → hecho
- ~~Inventario/estado~~ → `server/game_state.py` + panel + comando `INV`
- Pulir coherencia LLM con flags/lugares; saves opcionales

- **Cómo verificar:** `run_server.bat` + `curl http://127.0.0.1:8080/ping` + `RUN"aventura` en CPC
- **Riesgos:** IP PC hardcodeada en BASIC; Ollama debe estar arriba; firewall 8080; `.bas` ASCII puede necesitar tokenizar en emulador

---

## Objetivo del proyecto

Conectar un **Amstrad CPC real** a un LLM vía **M4 Board (Wi‑Fi)**:

1. El jugador escribe en lenguaje natural en el CPC  
2. Un servidor Python en el PC habla con **Ollama** (o modo mock)  
3. La respuesta vuelve empaquetada para ROM CPC (40 cols, ASCII, CRLF)  
4. El BASIC imprime texto y dispara `SOUND` en el chip **AY‑3‑8912**

Inspiración: aventuras conversacionales españolas de los 80, con parser sustituido por IA.

---

## Red actual (PoC)

| Nodo | IP / puerto |
|------|-------------|
| Gateway | `192.168.1.1` |
| PC (servidor) | `192.168.1.4` |
| M4 / CPC | `192.168.1.128` |
| HTTP juego | puerto **8080** |
| Ollama | `127.0.0.1:11434` |
| Modelo por defecto | `llama3.1:8b` |

Si cambia la IP del PC, editar la URL en `client/aventura.bas` (línea del `|HTTPGET`).

---

## Arquitectura

```text
CPC + M4                    PC
client/aventura.bas         server/server.py :8080
  INPUT ──HTTP GET──────►   ai_adventure.py → Ollama
  |HTTPGET → RESP.TXT ◄──   protocol + cpc_text
  parse T:/S:/E:
  PRINT + GOSUB SOUND
```

**Transporte elegido:** HTTP (`|HTTPGET` / `|HTTPMEM`), no TCP crudo en ASM (fase futura).

**Endpoints:**

| Ruta | Función |
|------|---------|
| `GET /ping` | Salud (`OK servidor ollama\|mock`) |
| `GET /turn?msg=...` | Turno de juego |
| `GET /reset` | Limpia historial de la IA |

---

## Protocolo de paquete

```text
T:linea1|linea2|linea3
S:2
E:0
```

- `T:` texto; líneas ≤40; separador `|`
- `S:` 0=neutro, 1=peligro, 2=ambiente, 3=objeto, 4=combate, 5=victoria
- `E:` 0 ok / 1 error
- **CRLF obligatorio** (`\r\n`): el CPC `LINE INPUT` corta en CR; solo LF provocaba `ERROR:` y basura tipo `:0 :0: :4`

---

## Estructura de carpetas (local)

```text
M4/
  README.md
  run_server.bat
  .gitignore
  client/aventura.bas
  server/
    server.py
    ai_adventure.py
    protocol.py
    cpc_text.py
    prompts/master.txt
    __init__.py
  tests/
  docs/
    CARGA.md
    SINTAXIA_HANDOFF.md   ← este archivo
    superpowers/plans/2026-08-02-aventura-ia-m4.md
  archivo/                ← material local, NO en Git
    docs_m4/  fotos/  carcasas/  rulezcharge/
```

**En GitHub solo va el motor** (no `archivo/`, no planes internos si están gitignored).

Tras reorganizar carpetas, **aún no se ha hecho push** de la nueva estructura; el repo remoto puede seguir con ficheros en la raíz antigua hasta el próximo push.

---

## Qué se implementó (cronología)

1. **Red M4:** Wi‑Fi OK en `192.168.1.128`; PC `192.168.1.4`
2. **Plan** HTTP vs TCP → HTTP; plan en `docs/superpowers/plans/…`
3. **Fase 1:** `protocol` + `cpc_text` + servidor mock `:8080`
4. **Fase 2–3:** `aventura.bas` (`|HTTPGET` → `RESP.TXT`, parseo, SOUND 0–5)
5. **Bug CRLF:** corregido en servidor + parser BASIC defensivo
6. **Fase 4:** Ollama (`ai_adventure.py`), historial corto, fallback error, `--mock`
7. **Nombre/repo:** SINTAXIA → push inicial a `kapi21/SINTAXIA`
8. **Ordenación local:** `client/`, `server/`, `archivo/`, `docs/`, `run_server.bat`

---

## Cómo arrancar (siguiente sesión)

### PC
```powershell
cd "C:\@MIS PROYECTOS\M4"
# Ollama debe responder en :11434
.\run_server.bat
# o: .\run_server.bat --mock
```

### Comprobar
```powershell
Invoke-WebRequest http://127.0.0.1:8080/ping -UseBasicParsing
Invoke-WebRequest "http://127.0.0.1:8080/turn?msg=miro+alrededor" -UseBasicParsing
```

### CPC
1. Copiar `client/aventura.bas` a la SD (tokenizar en emulador si hace falta)
2. `|NETSTAT` → `RUN"aventura`
3. Nueva partida IA: abrir `http://192.168.1.4:8080/reset` en el PC

Detalle extra: `docs/CARGA.md`.

---

## Decisiones de diseño a respetar

- Texto CPC-safe: sin tildes/ñ; wrap 40; respuestas cortas
- El PC **siempre** reempaqueta la salida del LLM (`repack_llm_text`)
- Sonido: el PC envía código; la tabla `SOUND` vive en BASIC
- BASIC 1.0-friendly: RSX vía variable (`|HTTPGET,@A$`)
- YAGNI PoC: una sesión en memoria, sin inventario complejo

---

## Próximos pasos sugeridos (priorizados)

1. **Push** de la estructura nueva a GitHub (`client/`, `server/`, …)
2. Ambiente visual CPC: `INK`/`BORDER`/`PAPER`, intro, borde según `S:`
3. Sonidos AY con `ENV`/`ENT` / ruido en combate
4. Panel web en el PC: elegir Ollama vs API OpenAI-compatible, modelo, reset
5. Comando `NUEVA` en BASIC → `/reset`
6. (Largo plazo) cliente TCP Z80 / `C_NET*`

---

## Archivos clave

| Archivo | Notas |
|---------|--------|
| `server/server.py` | HTTP; flags `--mock`, `--model` |
| `server/ai_adventure.py` | Ollama chat + historial + inferencia `S:` |
| `server/protocol.py` | `build_packet` / `parse_packet` (CRLF) |
| `server/cpc_text.py` | `normalize_cpc`, `wrap_lines` |
| `server/prompts/master.txt` | System prompt Master |
| `client/aventura.bas` | Cliente; IP PC en string URL |
| `README.md` | Doc pública del repo |
| `docs/CARGA.md` | Carga práctica en hardware |

---

## Notas operativas Windows

- Rutas con `@` y espacios: siempre `-LiteralPath` / comillas
- Preferir `run_server.bat` desde la raíz del workspace
- Material hardware (PDFs, zips, fotos, carcasas, RulezCharge) está en `archivo/` intacto
