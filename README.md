# SINTAXIA

> *"Del texto estructurado a la red neuronal: El retorno de la aventura conversacional a los 8 bits."*

<p align="center">
  <img src="server/web/hero.png" alt="SINTAXIA — aventura conversacional en Amstrad CPC" width="100%" />
</p>

<p align="center">
  <em>IA + Amstrad CPC + M4 Board · narrativa, inventario y chip AY-3-8912</em>
</p>

**SINTAXIA** conecta un **Amstrad CPC real** (464/6128) a un LLM (Ollama, OpenAI, Claude, Gemini, OpenRouter u API compatible) mediante la **[M4 Board](https://github.com/M4Duke/m4hardware)** (Wi‑Fi).

La IA genera la narrativa en lenguaje natural; el PC la empaqueta para el CPC (**40** u **80** columnas según el cliente, ASCII) y el cliente en Locomotive BASIC muestra el texto y dispara efectos en el chip **AY‑3‑8912**.

| Documento | Para quién |
|-----------|------------|
| [docs/GUIA_JUGADOR.md](docs/GUIA_JUGADOR.md) | Jugar sin tecnicismos |
| [docs/MANUAL.md](docs/MANUAL.md) | Instalación PC/CPC, panel, comandos |
| [docs/CARGA.md](docs/CARGA.md) | Copia rápida a la microSD |

**Clientes CPC:** launcher `sintaxia.bas` · `aventura.bas` (MODE 1) · `aventuramode2.bas` (MODE 2).

---

## Estructura del proyecto

```text
SINTAXIA/
  README.md
  run_server.bat
  client/
    sintaxia.bas          # launcher MODE 1 / 2
    aventura.bas          # MODE 1 (40 cols)
    aventuramode2.bas     # MODE 2 (80 cols, negro/verde)
    TITLE.SCR             # titulo MODE 1 (arte del proyecto)
    T2.SCR                # titulo MODE 2 (cabecera AMSDOS)
    TITLE2.SCR            # alias de T2.SCR
    ascii/                # copia de los .bas
  server/                 # HTTP :8080 + panel /ui
  tools/
    make_title_scr.py     # genera TITLE_gen.SCR (no pisa TITLE.SCR)
    make_title2_scr.py    # genera T2.SCR + TITLE2.SCR
    amsdos_header.py      # cabecera para LOAD en M4
  tests/
  docs/
  imagen/                 # arte fuente (PNG)
```

---

## Arquitectura

```text
Amstrad CPC + M4          PC (servidor)
─────────────────         ──────────────────────────
client/*.bas              server/server.py :8080
  INPUT  ──HTTP GET──►    Ollama / API / mock
  |HTTPGET ◄──────────    paquete T: / S: / E:
  PRINT + SOUND AY
```

---

## Requisitos

- PC con Python 3.10+
- [Ollama](https://ollama.com/) (p. ej. `llama3.1:8b`), otra API, o `--mock`
- Amstrad CPC + M4 Board en la misma LAN
- Firewall: TCP **8080** entrante

| Nodo (ejemplo) | IP |
|----------------|-----|
| PC servidor | `192.168.1.4` |
| M4 / CPC | `192.168.1.128` |

Ajusta `P$` en los `.bas` o usa **F7** / `HOST.TXT` en la SD.

---

## Arranque del servidor (PC)

```bat
run_server.bat
run_server.bat --mock
run_server.bat --model llama3.1:8b
```

**Panel:** [http://127.0.0.1:8080/ui](http://127.0.0.1:8080/ui) — proveedor, modelo, prompt, slots de partida, último paquete `T:/S:/E:`.

```bash
curl http://127.0.0.1:8080/ping
curl "http://127.0.0.1:8080/turn?msg=miro+alrededor"
```

---

## Cliente en el CPC (microSD)

Copia **en la misma carpeta** de la SD (sin subcarpeta `client/`):

```text
sintaxia.bas
aventura.bas
aventuramode2.bas
TITLE.SCR
T2.SCR
```

1. `|NETSTAT` — red OK  
2. `RUN"sintaxia` → **1** (MODE 1) o **2** (MODE 2)  
3. Titulo + **ESPACIO** → servidor → **Situacion** → escribe en español  

`T2.SCR` debe llevar **cabecera AMSDOS** (la genera `tools/make_title2_scr.py`). Sin ella, `LOAD` falla en la M4.  
`TITLE.SCR` (MODE 1) es el arte del proyecto; no lo regeneres a ciegas.

---

## Protocolo (cuerpo HTTP)

```text
T:linea1|linea2|linea3
S:2
E:0
```

- `T:` hasta **12** lineas; ancho 40 u 80 (`?cols=`)
- `S:` `0`–`5` (neutro, peligro, ambiente, objeto, combate, victoria)
- `E:` `0` ok / `1` error  
- Fin de linea: **CRLF**

---

## Sonidos AY (`S:`)

| Código | Efecto |
|--------|--------|
| 0 | Silencio |
| 1 | Peligro |
| 2 | Ambiente |
| 3 | Objeto |
| 4 | Combate |
| 5 | Victoria |

---

## Tests

```bash
cd tests
python -m pytest
```

---

## Roadmap breve

- (Hecho en demo-v1.1) Memoria de trama + ventana de historial mas larga
- (Futuro) Catálogo de aventuras fijas en servidor — [docs/IDEA_CATALOGO_AVENTURAS.md](docs/IDEA_CATALOGO_AVENTURAS.md)
- (Opcional) HTTPS PWA
- (Largo) cliente TCP Z80

---

## En la prensa

- [SINTAXIA: una aventura conversacional con IA llega al Amstrad CPC gracias a la M4](https://auamstrad.es/software/sintaxia-una-aventura-conversacional-con-ia/) — AUA / XeNoMoRPH (agosto 2026)

---

## Creditos / hardware

- M4 Board — [M4Duke/m4hardware](https://github.com/M4Duke/m4hardware)
- Inspirado en las aventuras conversacionales españolas de los 80
- Reportaje AUA — [auamstrad.es](https://auamstrad.es/software/sintaxia-una-aventura-conversacional-con-ia/) (XeNoMoRPH)

## Licencia

[MIT License](LICENSE)
