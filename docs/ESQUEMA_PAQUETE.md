# Esquema del paquete SINTAXIA (PC ↔ CPC)

Fecha: 2026-08-02

## Vista rapida

```text
T:linea1|linea2|linea3     ← lo que LEE el jugador en el Amstrad
S:2                        ← codigo de sonido AY (0-5)
E:0                        ← 0=sigue la partida, 1=error/fin
I:+objeto                  ← inventario (solo PC; opcional)
L:lugar                    ← lugar actual (solo PC; opcional)
F:clave=1                  ← marca si/no de historia (solo PC; opcional)
```

| Campo | ¿Lo ve el CPC? | Significado |
|-------|----------------|-------------|
| **T:** | Si | Narracion. Segmentos de max 40 chars unidos por `\|`. Max 12. |
| **S:** | Si (como SOUND) | Ambiente sonoro: 0 silencio … 5 victoria. |
| **E:** | Si (si error) | Estado: `0` ok, `1` problema / fin. |
| **I:** | No | Inventario: `+x` coge, `-x` deja, o lista `a,b,c`. |
| **L:** | No | Lugar actual de la partida. |
| **F:** | No | Flag (interruptor) `nombre=0` o `nombre=1`. |

## Detalle

### T: — Texto
Historia en segunda persona. Solo ASCII. El CPC imprime esto (typewriter).

### S: — Sonido
Tabla del cliente BASIC (`SOUND` / envolventes AY).

### E: — Error / fin
`0` continua. `1` el cliente puede marcar ERROR.

### I: — Inventario (flag de objetos, no confundir con F:)
Actualiza la mochila en el servidor.

### L: — Location
Donde esta el jugador para el Master.

### F: — Flags
Marcas de trama (`puerta_abierta=1`, `alarma=0`). No son objetos.

## Importante
Cada etiqueta en linea nueva. Nunca `T:.../S:2/E:0`.
