# Idea aparcada — Catálogo de aventuras fijas en servidor

**Fecha:** 2026-08-08  
**Estado:** aparcada (tormenta de ideas; no implementar aún)  
**Rama contexto:** `demo-v1.1`

## Resumen

Servidor con **varias aventuras concretas de autor**. El jugador elige en el CPC (ej. “La del dragón”) y juega contenido que vive en el servidor, no metido entero en el `.bas`.

## Decisiones ya tomadas

| Tema | Elección |
|------|----------|
| Tipo de aventura | **A — Fija / autor:** mapa, textos y reglas en el servidor. LLM opcional o ausente (no es el motor principal). |

## Pregunta abierta (cuando se retome)

Al elegir una aventura, ¿cómo llega el contenido?

- **A)** Paquete completo al empezar (simple; CPC sigue pidiendo turnos como ahora)
- **B)** Streaming por zonas/habitaciones
- **C)** Índice pequeño + textos bajo demanda

## Por qué no es “tontería” (ni obligatorio)

- Meter una sola historia en el `.bas` basta para una demo fija.
- Catálogo en servidor aporta: varias historias, actualizar sin regrabar SD, mundos grandes sin comerse la RAM del CPC.
- Con el modelo actual (100 % LLM libre), “descargar la aventura” aporta poco; con contenido **estructurado** (nodos/textos), sí.

## Relación con SINTAXIA hoy

Hoy el CPC es cliente fino HTTP; la “aventura” es prompt + LLM (+ `plot_summary`). Esta idea sería una **capa o modo paralelo**: motor de contenido autorado + catálogo, conviviendo o sustituyendo al modo LLM según se elija.

## Alcance sugerido al retomar (trocear)

1. Formato de aventura (habitaciones, objetos, verbos, finales) + 1 demo “El dragón”
2. API catálogo: listar / seleccionar / jugar turno
3. UX CPC: menú de aventuras tras el launcher
4. Solo después: streaming fino (B/C) si hace falta

## No hacer todavía

- No protocolo nuevo en el `.bas`
- No CMS ni tienda online
- No mezclar con el setup wizard salvo un selector futuro en `/ui`
