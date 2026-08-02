# Diseño: persistir ajustes del servidor

Fecha: 2026-08-02  
Proyecto: SINTAXIA  
Estado: aprobado

## Objetivo

Al cerrar y volver a abrir el servidor, recuperar proveedor IA, modelo, API key y resto de ajustes del panel (no solo Ollama por defecto).

## Decisiones

| Tema | Elección |
|------|----------|
| Almacenamiento | `server/settings.json` local, gitignored |
| API key | Incluida en claro en ese fichero (solo PC local) |
| Cuándo guardar | `POST /api/config` (Guardar) + cierre (`atexit` / Ctrl+C) |
| Cuándo cargar | Arranque del servidor |
| CLI | Flags explícitos pisan el fichero solo en esa sesión |

## Campos

`provider`, `model`, `ollama_url`, `api_base`, `api_key`, `temperature`, `mock`, `system`, `start_state`

No: historial de chat, slots de partida.

## Prioridad al arrancar

1. Defaults del código  
2. `settings.json` si existe  
3. Flags CLI presentes (`--provider`, `--model`, `--api-key`, `--api-base`, `--mock`)

## Seguridad

- Fichero en `.gitignore`  
- No loguear la API key al cargar/guardar
