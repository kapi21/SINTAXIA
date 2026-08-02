# Manual de SINTAXIA

**Aventura conversacional con IA para Amstrad CPC + M4 Board**

Versión del manual: 2026-08-02 v2  
Repositorio: https://github.com/kapi21/SINTAXIA

---

## Indice

1. [Que es SINTAXIA](#1-que-es-sintaxia)
2. [Como funciona (idea general)](#2-como-funciona-idea-general)
3. [Requisitos](#3-requisitos)
4. [Instalacion en el PC](#4-instalacion-en-el-pc)
5. [Instalacion en el Amstrad CPC](#5-instalacion-en-el-amstrad-cpc)
6. [Arranque del sistema](#6-arranque-del-sistema)
7. [Panel web (IU): guia de opciones](#7-panel-web-iu-guia-de-opciones)
8. [Jugar en el CPC](#8-jugar-en-el-cpc)
9. [Comandos del CPC](#9-comandos-del-cpc)
10. [Sonidos, colores y protocolo](#10-sonidos-colores-y-protocolo)
11. [Guardar y cargar partidas](#11-guardar-y-cargar-partidas)
12. [Problemas frecuentes](#12-problemas-frecuentes)

---

## 1. Que es SINTAXIA

SINTAXIA es un **motor / juego de aventura conversacional** pensado para un **Amstrad CPC real** (464, 664, 6128 o Plus) equipado con la tarjeta Wi‑Fi **M4 Board**.

En lugar de un parser rigido de verbos (`COGER LLAVE`, `IR NORTE` solo si estan en una lista), el jugador escribe **en lenguaje natural** (`miro alrededor`, `abro la puerta con cuidado`, `hablo con la sombra`). Un **modelo de lenguaje (LLM)** en el PC hace de *Master* de la aventura: narra, reacciona y mantiene coherencia con inventario, lugar y hechos de la partida.

El CPC se encarga de:

- Mostrar el texto (MODE 1, 40 columnas, ASCII sin tildes)
- Reproducir efectos en el chip **AY‑3‑8912**
- Cambiar el **borde** de pantalla segun el tono de la escena
- Enviar y recibir datos por la M4 via HTTP

El PC se encarga de:

- Hablar con **Ollama**, **OpenAI**, **Claude**, **Gemini**, una **API OpenAI-compatible**, o un modo **Mock** de prueba
- Empaquetar la respuesta para el CPC
- Guardar inventario, flags, lugar e historial corto
- Ofrecer un **panel web** de configuracion estilo CPC

Inspiracion: las aventuras conversacionales espanolas de los 80 (Don Quijote, El Jabato, etc.), llevadas a un flujo con IA en tiempo real.

---

## 2. Como funciona (idea general)

```text
  [ Jugador en el CPC ]
           |
           |  escribe: "miro la cueva"
           v
  aventura.bas  --HTTP GET-->  PC:8080/turn?msg=...
           ^                         |
           |                         v
           |                   Ollama / API / Mock
           |                         |
           |   RESP.TXT  <--- paquete T: / S: / E:
           |
     PRINT texto + SOUND AY + BORDER
```

1. El BASIC pide al servidor un turno.
2. El servidor consulta la IA (o el mock).
3. La respuesta vuelve en un formato fijo que el CPC entiende.
4. Se imprime el texto, suena el AY y cambia el borde.

Todo ocurre en la **misma Wi‑Fi** (LAN). No hace falta Internet si usas Ollama en local o el modo Mock.

---

## 3. Requisitos

### PC

| Elemento | Detalle |
|----------|---------|
| SO | Windows 10/11 (probado); Linux/macOS deberia funcionar con Python |
| Python | 3.10 o superior |
| Ollama (recomendado) | https://ollama.com — modelo tipico: `llama3.1:8b` |
| Red | Misma LAN que la M4; firewall permitiendo TCP **8080** |

### Amstrad CPC

| Elemento | Detalle |
|----------|---------|
| Maquina | CPC 464 / 664 / 6128 / Plus |
| Expansion | **M4 Board** con Wi‑Fi configurada |
| microSD | FAT32, con el cliente `aventura.bas` |
| Firmware M4 | Preferible reciente (comandos `|HTTPGET`, `|NETSTAT`) |

### Red de ejemplo (PoC)

| Equipo | IP |
|--------|-----|
| Router | `192.168.1.1` |
| PC (servidor) | `192.168.1.4` |
| M4 / CPC | `192.168.1.128` |
| Puerto del juego | `8080` |

Si tus IPs son distintas, cambia la del PC en `client/aventura.bas` (variable `P$`).

---

## 4. Instalacion en el PC

### 4.1 Obtener el codigo

```text
git clone https://github.com/kapi21/SINTAXIA.git
cd SINTAXIA
```

O descarga el ZIP del repositorio y descomprimelo.

Estructura relevante:

```text
SINTAXIA/
  run_server.bat
  client/aventura.bas
  server/
    server.py
    web/ui.html
    prompts/master.txt
    saves/          (partidas; se crean al guardar)
  docs/
    MANUAL.md       (este documento)
    CARGA.md
```

### 4.2 Python

Comprueba que Python esta en el PATH:

```powershell
python --version
```

No hace falta instalar paquetes extra: el servidor usa solo la biblioteca estandar.

### 4.3 Ollama (modo IA)

1. Instala Ollama.
2. Descarga un modelo, por ejemplo:

```powershell
ollama pull llama3.1:8b
```

3. Deja Ollama en marcha (suele escuchar en `http://127.0.0.1:11434`).

Si no quieres IA todavia, puedes arrancar en **modo Mock** (respuestas fijas por palabras clave).

### 4.4 Firewall Windows (importante)

El CPC debe poder conectar al PC en el puerto 8080. Ejemplo:

```powershell
New-NetFirewallRule -DisplayName "SINTAXIA CPC 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

### 4.5 Comprobar el servidor sin CPC

```powershell
cd ruta\a\SINTAXIA
.\run_server.bat
```

En otro terminal o navegador:

- http://127.0.0.1:8080/ui — panel
- http://127.0.0.1:8080/ping — debe devolver un paquete `T:OK...`

---

## 5. Instalacion en el Amstrad CPC

### 5.1 Configurar la M4 en Wi‑Fi

1. Inserta la microSD (FAT32) en la M4.
2. Enciende el CPC.
3. Configura red con `|NETSET` (o edita `m4/config.txt` en la SD).  
   Se recomienda **IP estatica**.
4. Comprueba con `|NETSTAT` que aparece la IP (ej. `192.168.1.128`).
5. Opcional: abre en el PC el navegador `http://IP-DE-LA-M4` (web UI de la M4).

Documentacion hardware: [M4Duke/m4hardware](https://github.com/M4Duke/m4hardware).

### 5.2 Copiar el cliente BASIC

1. En el PC, toma el fichero `client/aventura.bas`.
2. Copialo a la microSD de la M4 (raiz o una carpeta).
3. Si `RUN"aventura` **no** carga (ASCII sin cabecera AMSDOS):
   - Abre un emulador (WinAPE, CPCemu…), pega el listado, `SAVE"aventura`
   - Copia el `.bas` tokenizado a la SD
   - Alternativa: teclear en el CPC y `SAVE"aventura`
   - Alternativa: subir por la web UI de la M4

### 5.3 Ajustar la IP del PC en el BASIC

Abre `aventura.bas` y localiza:

```basic
30 P$="192.168.1.4:8080"
```

Sustituye `192.168.1.4` por la IP real de tu PC. El puerto debe ser `8080` salvo que lo cambies al arrancar el servidor.

---

## 6. Arranque del sistema

Orden recomendado:

1. **PC:** Wi‑Fi/LAN OK, Ollama OK (si usas IA).
2. **PC:** `run_server.bat` (o `cd server` + `python server.py`).
3. **PC (opcional):** abre http://127.0.0.1:8080/ui y revisa el modo/modelo.
4. **CPC:** `|NETSTAT` → `RUN"aventura`
5. En la intro del CPC debe salir **SERVIDOR ACTIVO**. Si no, pulsa `R` para reintentar o revisa IP/firewall.

### Variantes de arranque del servidor

| Comando | Efecto |
|---------|--------|
| `run_server.bat` | IA con Ollama, modelo por defecto |
| `run_server.bat --mock` | Sin LLM; respuestas por palabras clave |
| `run_server.bat --model llama3.1:8b` | Elige modelo Ollama |
| `run_server.bat --provider openai` | OpenAI oficial (`api.openai.com`; usa `--api-key`) |
| `run_server.bat --provider openai_compat` | API compatible (LM Studio, Ollama `/v1`, etc.) |
| `run_server.bat --provider claude` | Anthropic Claude (requiere `--api-key`) |
| `run_server.bat --provider gemini` | Google Gemini (requiere `--api-key`) |

Desde PowerShell:

```powershell
cd "C:\ruta\SINTAXIA\server"
python server.py --mock
python server.py --model llama3.1:8b --provider ollama
```

---

## 7. Panel web (IU): guia de opciones

URL local: **http://127.0.0.1:8080/** (redirige a `/ui`)  
URL en LAN: **http://IP-DEL-PC:8080/ui** (ej. `http://192.168.1.4:8080/ui`)

El panel imita un monitor CPC (borde azul, tipografia pixel, arte hero).

### 7.1 Panel izquierdo — Motor

| Control | Que hace |
|---------|----------|
| **Estado (READY…)** | Indica si el servidor responde, modo actual (MOCK / OLLAMA / OPENAI), modelo e historial corto (`H`). |
| **Modo → IA (LLM)** | Usa el proveedor y modelo configurados. |
| **Modo → Mock (sin IA)** | No llama al LLM. Respuestas fijas si detecta palabras (`cueva`, `espada`, `atacar`, `tesoro`…). Ideal para probar red y sonido. |
| **Proveedor → Ollama (local)** | API nativa de Ollama (`/api/chat`). Al seleccionar, carga modelos locales automáticamente. |
| **Proveedor → OpenAI** | API oficial `https://api.openai.com/v1` + API key. |
| **Proveedor → Claude** | Anthropic Messages API + API key (`x-api-key`). |
| **Proveedor → Gemini** | Google Generative Language + API key. |
| **Proveedor → Compatible** | Cualquier servidor tipo OpenAI (`/v1/chat/completions`: LM Studio, Ollama `/v1`, proxies…). |
| **Selector de Modelo** | Desplegable que se rellena al pulsar **Modelos ↺** o al cambiar proveedor. Al elegir uno se copia al campo de texto. |
| **Modelo (texto)** | Escribe el id del modelo a mano si no aparece en el selector (`llama3.1:8b`, `gpt-4o-mini`, `claude-haiku-4-5`, `gemini-2.0-flash`…). Tiene prioridad sobre el selector. |
| **Temperatura** | 0.0–2.0. Bajo = mas predecible; alto = mas inventivo (y a veces mas caotico). |
| **URL Ollama chat** | Por defecto `http://127.0.0.1:11434/api/chat`. Cambiala solo si Ollama esta en otra maquina/puerto. |
| **Base API** | URL base del proveedor cloud o compatible. Al cambiar proveedor el panel rellena un valor tipico. |
| **API key** | Clave OpenAI / Anthropic / Google. Solo en **memoria** del servidor. No hace falta con Ollama local. Al pegar la key, el panel carga los modelos automáticamente (debounce 700ms). |
| **System prompt** | Instrucciones del Master (formato `T:/S:/E:`, limites de texto, metadatos `I:/L:/F:`…). Puedes editarlo y pulsar **Guardar**. |
| **Guardar** | Aplica en el servidor la config del formulario (modo, proveedor, modelo, temperatura, URLs, prompt, key si la escribiste). Tras guardar recarga los modelos disponibles. |
| **Modelos ↺** | Consulta la API del proveedor actual y rellena el selector con los modelos disponibles. Para OpenAI/Claude/Gemini necesita la API key en el campo (o ya guardada en el servidor). |
| **Nueva** | Reinicia historial + inventario/lugar/flags (nueva partida). Equivale a `/reset`. |
| **Refresh** | Recarga estado mostrado sin cambiar config. |

### 7.2 Panel derecho — Paquete al CPC / partida

| Control | Que hace |
|---------|----------|
| **Estado partida** | Lugar actual, inventario y flags (p. ej. puertas abiertas). |
| **Partidas (slots 1-3)** | Resumen de partidas guardadas en el PC (`server/saves/`). |
| **nombre opcional** | Etiqueta al guardar (ej. `castillo`). |
| **Slot 1/2/3** | Elige que hueco usar. |
| **Guardar** (slot) | Guarda estado + historial corto en ese slot. |
| **Cargar** | Restaura ese slot en el servidor (afecta al siguiente turno del CPC). |
| **Listar** | Refresca la lista de slots. |
| **Jugador** | Ultimo mensaje recibido. |
| **Respuesta T:/S:/E:** | Ultimo paquete enviado (o generado) hacia el CPC. |
| **Error LLM** | Ultimo error de red/API si fallo la IA. |
| **Probar turno** | Envia un `/turn` desde el PC sin usar el CPC (depuracion). |

### 7.3 Flujo tipico en la IU

1. Arranca el servidor.
2. Abre `/ui`.
3. Elige **IA** + **Ollama** → el selector de modelos se rellena automáticamente → elige modelo → **Guardar**.
4. Para OpenAI/Claude/Gemini: elige proveedor → pega la **API key** (el panel carga modelos solos tras 0,7 s) → elige modelo del selector → **Guardar**.
5. O pulsa **Modelos ↺** en cualquier momento para recargar la lista.
6. Deja el panel abierto mientras juegas en el CPC: veras el ultimo paquete y el inventario actualizarse.
7. Usa **Guardar/Cargar** slot cuando quieras pausar la aventura.

---

## 8. Jugar en el CPC

### 8.1 Pantalla de introduccion

Al hacer `RUN"aventura`:

1. Paleta MODE 1 (fondo negro, texto ambar).
2. Titulo **SINTAXIA** y explicacion breve.
3. Lista de comandos.
4. **Comprobando servidor…** (ping a `/ping`).
5. Si OK: **SERVIDOR ACTIVO** y ejemplo `miro alrededor`.
6. Si falla: indica `run_server.bat`, IP esperada; `R` reintenta, **espacio** continua igual (sin garantia de red).

### 8.2 Bucle de juego

```text
> miro alrededor
Esperando al maestro...
(texto narrado en varias lineas)
(efecto de sonido + color de borde)
>
```

Escribes lo que haces **en espanol natural**. No hace falta sintaxis de parser clasico, aunque frases claras ayudan a la IA.

Limites practicos:

- Mensaje de jugador ~80 caracteres (URL BASIC).
- Respuesta: hasta **6 lineas** de **40** caracteres (si hay mas, el PC corta y puede anadir `...`).

### 8.3 Atmosfera y presentacion visual (Edicion Comercial AAA)

- **Efecto Typewriter (maquina de escribir)**: El texto narrativo aparece caracter a caracter acompanado de un sutil sonido de pulsacion en el chip AY-3-8912.
- **Tinta dinamica segun tono (`S:`)**:
  - `S=0` (neutro) / `S=2` (ambiente): Tinta ambar (`PEN 1`).
  - `S=1` (peligro) / `S=4` (combate): Tinta roja alerta (`PEN 3`).
  - `S=3` (objeto) / `S=5` (victoria): Tinta verde brillante (`PEN 2`).
- **Borde dinamico**: Cambia de color segun `S:` (peligro, cueva, tesoro, combate, victoria).
- **Animacion Pensando...**: Muestra feedback de puntos con tonos progresivos de audio antes de la peticion HTTP.
- **Paginacion automatica**: Tras 4 lineas impresas de respuesta, pausa la pantalla con `[ESPACIO para continuar]`.
- **Efecto CRT Flash**: Destello inicial de pantalla al arrancar el programa.
- **SOUND** con envolventes `ENV`/`ENT` (peligro grave, eco, arpegio, golpe+ruido, fanfarria).

---

## 9. Comandos del CPC

Todo se escribe en el prompt `>` (mayusculas/minusculas toleradas en la mayoria).

### 9.1 Comandos de sistema

| Comando | Accion |
|---------|--------|
| `AYUDA` | Muestra ayuda e IP del servidor (`P$`). |
| `NUEVA` | Pide `/reset`: nueva partida (limpia historial y estado en el PC). |
| `INV` / `inventario` / `objetos` | Lista lo que llevas (sin llamar a la IA). |
| `SAVE 1` … `SAVE 3` | Guarda partida en ese slot (tambien `GUARDAR 1`). |
| `LOAD 1` … `LOAD 3` | Carga ese slot (tambien `CARGAR 1`). |
| `SAVES` / `PARTIDAS` | Lista slots ocupados/vacios. |
| `!` | Repite el ultimo comando introducido. |
| `D` / `DEBUG` | Pantalla de diagnostico (IP host, ultima URL, turnos, estado red). |
| `QUIT` | Sale del programa. |

Cualquier otra frase se interpreta como **accion de aventura** y se envia a `/turn`.

### 9.2 Ejemplos de acciones

```text
miro alrededor
voy al norte
abro la puerta
cojo la antorcha
hablo con el guardian
atacar
uso la llave en la cerradura
```

En modo Mock, ciertas palabras disparan escenas fijas (`cueva`, `espada`, `atacar`, `peligro`, `tesoro`…).

### 9.3 Que ocurre “detras” en una accion

1. Se codifica el mensaje (espacios → `+`).
2. `|HTTPGET` descarga la respuesta a `RESP.TXT`.
3. Se leen lineas `T:`, `S:`, `E:`.
4. Se imprimen las lineas de texto (separador `|`).
5. Suena el AY y cambia el borde.

Metadatos que la IA puede enviar (`I:+llave`, `L:cripta`, `F:puerta=1`) **los procesa solo el PC**; el CPC no los muestra.

---

## 10. Sonidos, colores y protocolo

### 10.1 Codigo de sonido `S:`

| S | Significado | Efecto tipico |
|---|-------------|----------------|
| 0 | Neutro | Silencio |
| 1 | Peligro | Tono grave + envolvente |
| 2 | Ambiente / cueva | Eco suave (2 canales) |
| 3 | Objeto | Arpegio |
| 4 | Combate | Golpe + ruido |
| 5 | Victoria / logro | Fanfarria |

### 10.2 Paquete hacia el CPC

```text
T:linea1|linea2|linea3
S:2
E:0
```

- `E:0` = ok · `E:1` = error (mensaje en `T:`)
- Fin de linea **CRLF** (importante para `LINE INPUT`)

### 10.3 Estado de partida (PC)

- **Lugar** (`L:`)
- **Inventario** (`I:+obj` / `I:-obj` / lista)
- **Flags** (`F:clave=1`)

Visibles en el panel; consultables en CPC con `INV` (inventario).

---

## 11. Guardar y cargar partidas

- **Donde se guardan:** ficheros JSON en `server/saves/slot1.json` … `slot3.json` (en el PC).
- **Que se guarda:** lugar, inventario, flags + historial corto del chat (no la API key).
- **Desde CPC:** `SAVE 2`, `LOAD 2`, `SAVES`.
- **Desde panel:** bloque Partidas → elegir slot → Guardar / Cargar.

Si cargas un slot vacio: mensaje de error (`E:1`).

---

## 12. Problemas frecuentes

| Sintoma | Que revisar |
|---------|-------------|
| Intro: SERVIDOR NO ACTIVO | `run_server.bat` en marcha; `P$` = IP del PC; firewall 8080; misma Wi‑Fi |
| `Fallo red/archivo` | M4 conectada (`|NETSTAT`); servidor en `0.0.0.0:8080` |
| Texto cortado o `...` | Limite 6×40 del protocolo; normal si la IA escribe de mas |
| Texto basura / ERROR: raro | Servidor antiguo sin CRLF; actualiza y reinicia `server.py` |
| IA no responde | Ollama arriba; modelo correcto; panel en modo IA; mira **Error LLM** |
| Mock siempre igual | Es normal sin palabras clave; cambia a modo IA |
| `RUN"aventura` no carga | Tokeniza el BASIC en emulador o teclea y `SAVE` |
| Load no restaura en CPC | El load afecta al **servidor**; el siguiente turno en CPC ya usa ese estado |
| Panel no responde / congelado | Reinicia `server.py`; en sesiones antiguas el lock bloqueaba el panel durante el turno LLM — resuelto en v2 |
| Selector modelos vacio (Ollama) | Ollama debe estar arriba; pulsa **Modelos ↺**; mira consola del servidor para el error exacto |
| Selector modelos vacio (cloud) | Introduce la API key → espera 1 s → se cargan solos; o pulsa **Modelos ↺** con la key en el campo |

### Prueba minima de red desde el CPC

```basic
a$="@192.168.1.4:8080/ping>PING.TXT"
|HTTPGET,@a$
OPENIN "PING.TXT"
LINE INPUT #9,a$:PRINT a$:CLOSEIN
```

Deberia verse algo como `T:OK servidor ...`.

---

## Referencias rapidas

| Recurso | Ruta / URL |
|---------|------------|
| Panel | http://127.0.0.1:8080/ui |
| Cliente CPC | `client/aventura.bas` |
| Arranque PC | `run_server.bat` |
| Notas cortas SD | `docs/CARGA.md` |
| Handoff tecnico | `docs/SINTAXIA_HANDOFF.md` |
| Hardware M4 | https://github.com/M4Duke/m4hardware |
| Codigo | https://github.com/kapi21/SINTAXIA |

---

*Fin del manual. Que la antorcha no se apague.*
