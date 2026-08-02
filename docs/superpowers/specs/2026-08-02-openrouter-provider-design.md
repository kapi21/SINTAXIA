# Diseño: proveedor LLM OpenRouter

Fecha: 2026-08-02  
Proyecto: SINTAXIA  
Estado: aprobado (pendiente implementación)

## Objetivo

Añadir **OpenRouter** como proveedor de IA de primera clase en el servidor y el panel web, usando la API key del usuario (memoria / `--api-key`), sin cambiar el protocolo CPC ni el empaquetado `T:/S:/E:`.

## Decisiones

| Tema | Elección |
|------|----------|
| Exposición en panel | Opción propia **OpenRouter** (no solo Compatible) |
| Modelo por defecto | `openrouter/auto` |
| API key | Igual que OpenAI: panel o `--api-key`; solo en memoria; sin env var |
| Transporte | Reutilizar cliente OpenAI-compatible (`/v1/chat/completions`, Bearer) |
| Fuera de alcance | Streaming, routing avanzado OpenRouter, guardar key a disco, `OPENROUTER_API_KEY` |

## Arquitectura

OpenRouter es un valor más de `provider`, al mismo nivel que `openai` / `claude` / `gemini`.

| Pieza | Cambio |
|--------|--------|
| `server/llm_providers.py` | Incluir `openrouter` en `PROVIDERS` y `DEFAULTS` |
| `server/ai_adventure.py` | Tratar `openrouter` como path OpenAI-compat en chat y listado de modelos; headers de atribución |
| `server/server.py` | `--provider` acepta `openrouter` |
| `server/web/ui.html` | Opción, preset, `NEEDS_KEY` |
| Docs | MANUAL (+ handoff/guía si listan proveedores) |

Flujo: panel guarda provider/key/modelo → `AdventureAI` → `POST {api_base}/chat/completions` → mismo `repack_llm_text` / estado de partida.

## Defaults

```text
provider: openrouter
api_base: https://openrouter.ai/api/v1
model:    openrouter/auto
label:    OpenRouter
```

## Componentes

### Chat y modelos

- `Authorization: Bearer <api_key>`
- Chat: `POST …/chat/completions` (mismo payload/extracción que OpenAI)
- Modelos: `GET …/models` (mismo path que `openai` / `openai_compat`)
- Si `provider == "openrouter"`, añadir headers de atribución (opcionales para la API; recomendados por OpenRouter):
  - `HTTP-Referer: https://github.com/kapi21/SINTAXIA`
  - `X-OpenRouter-Title: SINTAXIA`
- Exigir API key en UI (`NEEDS_KEY`) igual que OpenAI

### UI / CLI

- Selector: nueva opción OpenRouter; al cambiar, rellenar `api_base` y modelo por defecto
- Arranque: `run_server.bat --provider openrouter --api-key …` (o pegar key en panel y Guardar)

## Errores

- Sin API key: el panel bloquea Guardar/Modelos como con OpenAI
- Key inválida / cuota / modelo: error HTTP → campo “Error LLM” / paquete `E:1` en CPC (camino existente)
- Fallo al listar modelos: toast/error en panel; el servidor no cae

## Verificación

1. Panel → OpenRouter → pegar key → **Modelos ↺** lista modelos
2. Modelo `openrouter/auto` → Guardar → turno de prueba o Generar prompt
3. CPC / panel: respuesta `T:` normal; sin cambios de protocolo

## No hacer

- Nuevo cliente HTTP aparte del path OpenAI-compat
- Persistencia de API keys en disco
- Cambios en `aventura.bas` o esquema del paquete
