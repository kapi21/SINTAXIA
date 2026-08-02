# SINTAXIA

> *"Del texto estructurado a la red neuronal: El retorno de la aventura conversacional a los 8 bits."*

**SINTAXIA** conecta un **Amstrad CPC real** (464/6128) a un LLM (Ollama u otro) mediante la **[M4 Board](https://github.com/M4Duke/m4hardware)** (Wi‑Fi).

La IA genera la narrativa en lenguaje natural, el PC la empaqueta para el CPC (40 columnas, ASCII) y el cliente en Locomotive BASIC muestra el texto y dispara efectos en el chip **AY‑3‑8912**.

---

## Arquitectura

```text
Amstrad CPC + M4          PC (servidor)
─────────────────         ──────────────────────────
aventura.bas              server.py :8080
  INPUT  ──HTTP GET──►    Ollama / mock
  |HTTPGET ◄──────────    paquete T: / S: / E:
  PRINT + SOUND AY
```

| Pieza | Rol |
|--------|-----|
| `aventura.bas` | Cliente CPC (MODE 1, HTTP M4, parseo, SOUND) |
| `server.py` | HTTP en puerto 8080 |
| `ai_adventure.py` | Ollama + historial + reempaquetado |
| `protocol.py` / `cpc_text.py` | Contrato de paquete y texto CPC-safe |
| `prompts/master.txt` | System prompt del Master |

## Protocolo (cuerpo HTTP)

```text
T:linea1|linea2|linea3
S:2
E:0
```

- `T:` descripción; líneas ≤40 chars, separadas por `|` (máx. ~4)
- `S:` sonido `0`–`5` (neutro, peligro, ambiente, objeto, combate, victoria)
- `E:` `0` ok / `1` error  
- Fin de línea: **CRLF** (requerido por `LINE INPUT` del CPC)

---

## Requisitos

- PC con Python 3.10+
- [Ollama](https://ollama.com/) (recomendado: `llama3.1:8b`) o modo `--mock`
- Amstrad CPC + M4 Board en la misma LAN
- Firewall Windows: permitir TCP **8080** entrante

IPs de ejemplo usadas en el PoC:

| Nodo | IP |
|------|-----|
| PC servidor | `192.168.1.4` |
| M4 / CPC | `192.168.1.128` |

Ajusta la IP del PC en la línea 150 de `aventura.bas` si cambia.

---

## Arranque del servidor (PC)

```bash
cd SINTAXIA
python server.py                  # Ollama, modelo por defecto llama3.1:8b
python server.py --model llama3.1:8b
python server.py --mock           # sin IA (respuestas por palabras clave)
```

Prueba rápida:

```bash
curl http://127.0.0.1:8080/ping
curl "http://127.0.0.1:8080/turn?msg=miro+alrededor"
curl http://127.0.0.1:8080/reset
```

---

## Cliente en el CPC

1. Copia `aventura.bas` a la microSD de la M4  
   (si no carga como ASCII, `SAVE"aventura` desde un emulador y copia el `.bas` tokenizado)
2. En el CPC: `|NETSTAT` y comprueba IP
3. `RUN"aventura`
4. Escribe acciones en español natural (`miro alrededor`, `voy al norte`, …). `QUIT` para salir.

Prueba manual de red desde BASIC:

```basic
a$="@192.168.1.4:8080/ping>PING.TXT"
|HTTPGET,@a$
OPENIN "PING.TXT"
LINE INPUT #9,a$:PRINT a$:CLOSEIN
```

---

## Sonidos AY (`S:`)

| Código | Efecto |
|--------|--------|
| 0 | Silencio |
| 1 | Pitido grave (peligro) |
| 2 | Ambiente / cueva |
| 3 | Arpegio (objeto) |
| 4 | Golpe (combate) |
| 5 | Fanfarria (victoria) |

---

## Tests

```bash
python -c "from protocol import build_packet, parse_packet; print(parse_packet(build_packet(['Hola'],2)))"
```

---

## Roadmap breve

- Ambiente visual CPC (tintas, borde según `S:`)
- Sonidos AY con envolventes
- Panel web en el PC (Ollama vs API externa)
- Inventario / estado de partida más rico

---

## Créditos / hardware

- M4 Board — [M4Duke/m4hardware](https://github.com/M4Duke/m4hardware)
- Inspirado en la tradición de aventuras conversacionales españolas de los 80

## Licencia

A definir por el mantenedor del repositorio.
