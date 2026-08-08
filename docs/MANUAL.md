# Manual de SINTAXIA

**Aventura conversacional con IA para Amstrad CPC + M4 Board**

Versión del manual: 2026-08-07 v6  
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

- Mostrar el texto (MODE 1 / MODE 2, ASCII sin tildes)
- Reproducir efectos en el chip **AY‑3‑8912**
- Mantener **borde negro**
- Enviar y recibir datos por la M4 via HTTP

El PC se encarga de:

- Hablar con **Ollama**, **OpenAI**, **Claude**, **Gemini**, **OpenRouter**, una **API OpenAI-compatible**, o un modo **Mock** de prueba
- Empaquetar la respuesta para el CPC
- Guardar inventario, flags, lugar, historial reciente y memoria de trama
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
4. Se imprime el texto y suena el AY.

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
| microSD | FAT32; `.bas` + `TITLE.SCR` / `T2.SCR` en la **misma carpeta** (sin subcarpeta `client/` en la tarjeta) |
| Firmware M4 | Preferible reciente (comandos `|HTTPGET`, `|NETSTAT`) |

### Red de ejemplo (PoC)

| Equipo | IP |
|--------|-----|
| Router | `192.168.1.1` |
| PC (servidor) | `192.168.1.4` |
| M4 / CPC | `192.168.1.128` |
| Puerto del juego | `8080` |

Si tus IPs son distintas, cambia la del PC en `client/aventura.bas` o `aventuramode2.bas` (`P$`).

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
  client/
    sintaxia.bas
    aventura.bas
    aventuramode2.bas
    TITLE.SCR          (MODE 1; arte manual)
    T2.SCR             (MODE 2; AMSDOS)
    TITLE2.SCR         (alias MODE 2)
    ascii/             (copia de los .bas)
  tools/
    make_title_scr.py
    make_title2_scr.py
    amsdos_header.py
  server/
    server.py
    web/ui.html
    prompts/master.txt
    saves/
  docs/
    MANUAL.md
    GUIA_JUGADOR.md
    CARGA.md
    SINTAXIA_HANDOFF.md
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

1. En el PC, copia a la microSD de la M4 (**todos en el mismo directorio**; la ruta `client/` existe solo en el PC):
   - `client/sintaxia.bas` — **launcher** (entrada recomendada: elige MODE 1 o 2)
   - `client/aventura.bas` — cliente **MODE 1** (40 columnas)
   - `client/aventuramode2.bas` — cliente **MODE 2** (80 columnas; negro/verde)
   - `client/TITLE.SCR` — titulo grafico MODE 1 (arte del proyecto / manual; con cabecera AMSDOS)
   - `client/T2.SCR` — titulo grafico MODE 2 (**recomendado**; cabecera AMSDOS; 16512 bytes)
   - `client/TITLE2.SCR` — alias opcional del mismo dump MODE 2
2. En ambos clientes revisa `P$` (IP del PC). El de MODE 2 pide `?cols=80` al servidor.
3. Si `RUN"sintaxia` / `RUN"aventura` **no** carga (ASCII sin cabecera AMSDOS del BASIC):
   - Abre un emulador (WinAPE, CPCemu…), carga el listado, `SAVE"sintaxia` (o `aventura`)
   - Alternativa: teclear en el CPC y `SAVE"…`
   - Alternativa: subir por la web UI de la M4
   - `aventuramode2.bas` debe guardarse con **CRLF**
4. **Importante SCR:** sin cabecera AMSDOS, `LOAD"T2.SCR",&C000` falla en la M4. Regenerar MODE 2 con `python tools/make_title2_scr.py`. El titulo MODE 1 (`TITLE.SCR`) es **arte controlado a mano**; no lo pises con el generador salvo `--force` (por defecto escribe `TITLE_gen.SCR`).

### 5.3 Ajustar la IP del PC en el BASIC

Abre `aventura.bas` o `aventuramode2.bas` y localiza:

```basic
30 P$="192.168.1.4:8080"
```

Sustituye `192.168.1.4` por la IP real de tu PC. El puerto debe ser `8080` salvo que lo cambies al arrancar el servidor.

---

## 6. Arranque del sistema

Orden recomendado:

1. **PC:** Wi‑Fi/LAN OK, Ollama OK (si usas IA).
2. **PC:** `run_server.bat` (o `cd server` + `python server.py`).
3. **PC:** abre http://127.0.0.1:8080/ui  
   - **Primera vez** (sin `settings.json` o tras reconfigurar): el **asistente de configuracion** es obligatorio (motor, narrativa, IP/puerto para el CPC). Hasta terminarlo, el CPC solo puede hacer `/ping`; `/intro` y `/turn` responden error.  
   - Si ya hay config: panel normal. Boton **Reconfigurar…** borra config + estado + slots (hay que escribir `RECONFIGURAR`).
4. **CPC:** `|NETSTAT` → `RUN"sintaxia` → **1** o **2**  
   (o `RUN"aventura` / `RUN"aventuramode2` en directo)
5. En la intro del CPC debe salir **SERVIDOR ACTIVO**. Si no, pulsa `R` para reintentar o revisa IP/firewall.

### Variantes de arranque del servidor

| Comando | Efecto |
|---------|--------|
| `run_server.bat` | Carga `server/settings.json` si existe; si no, abre el asistente en `/ui`. Abre el navegador |
| `run_server.bat --no-browser` | Igual sin abrir el navegador |
| `run_server.bat --mock` | Sin LLM; respuestas por palabras clave (pisa settings en esa sesion; no salta el asistente si falta setup) |
| `run_server.bat --model llama3.1:8b` | Elige modelo (pisa settings) |
| `run_server.bat --provider openai` | OpenAI oficial (`api.openai.com`; usa `--api-key`) |
| `run_server.bat --provider openrouter` | OpenRouter (`openrouter.ai`; usa `--api-key`) |
| `run_server.bat --provider openai_compat` | API compatible (LM Studio, Ollama `/v1`, etc.) |
| `run_server.bat --provider claude` | Anthropic Claude (requiere `--api-key`) |
| `run_server.bat --provider gemini` | Google Gemini (requiere `--api-key`) |
| `run_server.bat --port 9090` | Fuerza puerto (si no se pasa, usa `preferred_port` del asistente o 8080) |

Los flags CLI solo afectan a **esa** sesion; al **Guardar**, al **Finalizar** el asistente o al cerrar el servidor se vuelve a escribir `settings.json` con lo que haya en memoria. El `preferred_port` del asistente se aplica en el **siguiente** arranque (salvo que pases `--port`).


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

**Movil (misma Wi‑Fi):** abre la URL LAN en Chrome/Safari → menu → **Anadir a pantalla de inicio** / **Instalar app**. Usa el icono de `imagen/icon.png` (manifest en `/assets/manifest.webmanifest`). Sin HTTPS no hay PWA “completa”, pero queda como acceso a pantalla completa.

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
| **Proveedor → OpenRouter** | `https://openrouter.ai/api/v1` + API key. Modelo por defecto `openrouter/auto`. |
| **Proveedor → Compatible** | Cualquier servidor tipo OpenAI (`/v1/chat/completions`: LM Studio, Ollama `/v1`, proxies…). |
| **Selector de Modelo** | Desplegable que se rellena al pulsar **Modelos ↺** o al cambiar proveedor. Al elegir uno se copia al campo de texto. |
| **Modelo (texto)** | Escribe el id del modelo a mano si no aparece en el selector (`llama3.1:8b`, `gpt-4o-mini`, `claude-haiku-4-5`, `gemini-2.0-flash`…). Tiene prioridad sobre el selector. |
| **Temperatura** | 0.0–2.0. Bajo = mas predecible; alto = mas inventivo (y a veces mas caotico). |
| **URL Ollama chat** | Por defecto `http://127.0.0.1:11434/api/chat`. Cambiala solo si Ollama esta en otra maquina/puerto. |
| **Base API** | URL base del proveedor cloud o compatible. Al cambiar proveedor el panel rellena un valor tipico. |
| **API key** | Clave OpenAI / Anthropic / Google / OpenRouter. Se guarda en `server/settings.json` (local, no va a Git) al pulsar **Guardar** y al cerrar el servidor. No hace falta con Ollama local. Al pegar la key, el panel carga los modelos automáticamente (debounce 700ms). |
| **System prompt** | Instrucciones del Master. Editable a mano. Ver tambien **Generar prompt** / **Prompt por defecto**. |
| **Generar prompt** | La IA inventa solo el **mundo** (tema, tono, lugar…); el servidor anade las **reglas fijas** (`prompts/rules_fixed.txt`) y un **estado inicial** (lugar/inventario/flags). Revisa el texto y pulsa **Guardar**. |
| **Prompt por defecto** | Restaura `prompts/master.txt` + estado clasico (entrada del castillo). Luego **Guardar**. |
| **Guardar** | Aplica config (y el `start_state` pendiente si viniste de Generar/Por defecto) y la escribe en `server/settings.json` para el proximo arranque. |
| **Modelos ↺** | Consulta la API del proveedor actual y rellena el selector. |
| **Nueva** | Reinicia la partida al **mundo base** actual del servidor (`/reset` / `start_state`). |
| **Refresh** | Recarga estado mostrado sin cambiar config. |

### 7.2 Panel derecho — Paquete al CPC / partida

| Control | Que hace |
|---------|----------|
| **Estado partida** | Lugar actual, inventario y flags (p. ej. puertas abiertas). |
| **Partidas (slots 1-3)** | Resumen de partidas guardadas en el PC (`server/saves/`). |
| **nombre opcional** | Etiqueta al guardar (ej. `castillo`). |
| **Slot 1/2/3** | Elige que hueco usar. |
| **Guardar** (slot) | Guarda mundo (`system`/`start_state`) + estado + historial + memoria de trama. |
| **Cargar** | Restaura ese slot **en memoria** (no escribe `settings.json`). |
| **Listar** | Refresca la lista de slots. |
| **Jugador** | Ultimo mensaje recibido. |
| **Respuesta T:/S:/E:** | Ultimo paquete enviado (o generado) hacia el CPC. |
| **Error LLM** | Ultimo error de red/API si fallo la IA. |
| **Probar turno** | Envia un `/turn` desde el PC sin usar el CPC (depuracion). |

### 7.3 Persistencia de ajustes (`settings.json`)

Al pulsar **Finalizar** en el asistente, **Guardar** en el panel (y al cerrar el servidor) se escribe `server/settings.json` en el PC:

- `setup_complete`, `preferred_port` (asistente)
- proveedor, modelo, URLs, temperatura, modo mock  
- **API key** (en claro; fichero local, **no** se sube a Git)  
- system prompt y `start_state` (mundo base)

Al arrancar de nuevo, el servidor carga ese fichero. Veras en consola `SETTINGS cargados…` y el proveedor/modelo recordados. Si falta setup: `SETUP required → http://127.0.0.1:PUERTO/ui`.

No confundir con las **partidas** (`server/saves/slotN.json`): ahi va el **mundo de esa partida** + inventario/historial/`plot_summary`. El LOAD de un slot pone ese mundo en RAM; **Guardar** del panel es lo que persiste el default en `settings.json`. **Reconfigurar…** borra settings (stub) + slots.

### 7.4 Flujo tipico en la IU

1. Arranca el servidor.
2. Abre `/ui`. Si aparece el asistente, completalo (Mock o IA → narrativa → red/CPC → Finalizar).
3. Con el panel ya abierto: ajusta modelo/prompt y **Guardar** cuando quieras.
4. Deja el panel abierto mientras juegas en el CPC.
5. Usa **Guardar/Cargar** slot (partidas) cuando quieras pausar la aventura.
6. Si quieres empezar de cero en el PC: **Reconfigurar…** (escribe `RECONFIGURAR`).

---

## 8. Jugar en el CPC

### 8.1 Pantalla de introduccion

Al hacer `RUN"sintaxia` aparece el menu de modo. Al pulsar **1** o **2** muestra **Seleccionado Modo…** e **Iniciando la aventura…** mientras carga el cliente.

Con **1** / `RUN"aventura` (MODE 1):

1. Mensaje **Iniciando la aventura...**
2. Paleta MODE 1 (borde negro).
3. (Opcional) Splash grafico `TITLE.SCR` con **tema AY de intro** (~2 min, bucle hasta ESPACIO).
4. Pantalla de ayuda corta (comandos + IP `P$`) → **ESPACIO**.
5. **Comprobando servidor…** (`/ping`).
6. Si OK: **SERVIDOR ACTIVO** → **Situacion** (`/intro`).
7. Si falla: `R` reintenta, **espacio** continua sin garantia de red.

`RUN"aventuramode2` (MODE 2, 80 cols, negro/verde):

1. **Iniciando la aventura...**
2. Splash `T2.SCR` (o `TITLE2.SCR`) si estan en la SD; si no, cartel tipografico Dinamic.
3. Misma musica / **ESPACIO** y el resto del flujo. URLs con `?cols=80`.

Nota CPC: al editar los `.bas` en ASCII, evita numeros de linea **>32767**. `aventuramode2.bas` debe guardarse con **CRLF**.

### 8.2 Bucle de juego

```text
> miro alrededor
Pensando /-\|
(texto narrado letra a letra; una tecla lo acelera)
(efecto de sonido AY segun S:)
>
```

La entrada usa un **editor por teclado** (no el `INPUT` clasico): puedes borrar con DEL/backspace. Softkeys: **F1**=`INV`, **F2**=`AYUDA`, **F3**=`SAVE 1`, **F4**=`LOAD 1`, **F5**=`NUEVA`, **F6**=`SONIDO` (ON/OFF), **F7**=`IP`, **F8**=`QUIT`, **F9**=`RAPIDO` (toggle texto rapido). **Flechas** = historial (5). `MUTE` silencia. `LENTO` fuerza typewriter. IP del PC: linea `P$` en el `.bas`, o fichero **`HOST.TXT`** en la SD (una linea `IP:puerto`); **F7** edita y guarda ese fichero.

Escribes lo que haces **en espanol natural**. No hace falta sintaxis de parser clasico, aunque frases claras ayudan a la IA.

Limites practicos:

- Mensaje de jugador ~80 caracteres (URL BASIC); editor limita a ~60 en pantalla.
- Respuesta: hasta **12 lineas**; ancho **40** (MODE 1) u **80** (MODE 2 via `?cols=80`). El PC rellena el ancho (reflow) y omite segmentos vacios.

### 8.3 Atmosfera y presentacion visual

- **Typewriter**: texto caracter a caracter + clic AY; **cualquier tecla** acelera.
- **Cursor de prompt**: bloque `CHR$(143)` parpadeante.
- **Borde**: siempre **negro**.
- **Clientes**: `sintaxia.bas`; `aventura.bas` + `TITLE.SCR`; `aventuramode2.bas` + `T2.SCR`.
- **AYUDA / F2**: imprime debajo del texto actual (**sin CLS**); lista completa **sin** pausa “Pulsa ESPACIO”.
- **Ancho dinamico**: `?cols=40|80` + reflow en el PC.
- **Animacion Pensando...**: spinner `/-\|` antes del HTTP.
- **Tema de titulo** (~2 min) + pedal en ayuda.
- **SOUND** con envolventes `ENV`/`ENT` segun `S:` / `E:1`.
- Viñetas `PLOT`/`DRAW` y cabecera fija in-game: **no activas** (experimento en `archivo/presencia_ui/`).

---

## 9. Comandos del CPC

Todo se escribe en el prompt `>` (mayusculas/minusculas toleradas en la mayoria).

### 9.1 Comandos de sistema

| Comando | Accion |
|---------|--------|
| `AYUDA` / **F2** | Lista de comandos debajo del texto (sin CLS ni pausa de pagina). |
| `NUEVA` / `REINICIO` / **F5** | Pide **S/N**; si S: `/reset` + `/intro`. |
| `INV` / `inventario` / `objetos` / **F1** | Lista lo que llevas (sin llamar a la IA). |
| `SAVE 1` … `SAVE 3` / **F3**=`SAVE 1` | Guarda partida en ese slot. |
| `LOAD 1` … `LOAD 3` / **F4**=`LOAD 1` | Carga ese slot. |
| `SAVES` / `PARTIDAS` | Lista slots ocupados/vacios. |
| `!` / **flechas ARR/ABJ** | Historial de hasta 5 comandos (`!` = el mas reciente). |
| `D` / `DEBUG` | Pantalla de diagnostico (IP host, ultima URL, turnos, historial, estado red). |
| `QUIT` / **F8** | Pide **S/N** («Salir sin guardar?»); si S: vuelve a la bienvenida (no guarda, no reinicia el CPC). |
| `MUTE` / `SILENCIO` | Apaga efectos AY. |
| `SONIDO` / `AUDIO` / **F6** | Alterna sonido ON/OFF. |
| `IP` / `HOST` / **F7** | Edita `P$` y escribe `HOST.TXT` en la SD. |
| `RAPIDO` / **F9** | Alterna texto rapido persistente (`FA%`). |
| `LENTO` | Typewriter letra a letra. |

Softkeys **F1**–**F9** se definen al arrancar (`KEY`). Bienvenida: atajos cortos; **F2**/`AYUDA` muestra la lista completa (paginada). Turnos largos piden **ESPACIO** cada ~11 lineas. Con **RAPIDO**/**F9** cada linea se imprime de golpe. Al arrancar se lee `HOST.TXT` si existe.

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
5. Suena el AY (borde permanece negro).

Metadatos que la IA puede enviar (`I:+llave`, `L:cripta`, `F:puerta=1`) **los procesa solo el PC**; el CPC no los muestra.

---

## 10. Sonidos, colores y protocolo

### 10.1 Codigo de sonido `S:`

| S | Significado | Efecto tipico |
|---|-------------|----------------|
| 0 | Neutro | Silencio |
| 1 | Peligro | Acorde grave 2 canales (sombrío) |
| 2 | Ambiente / cueva | Eco suave (2 canales) |
| 3 | Objeto | Arpegio agudo corto |
| 4 | Combate | Golpe + ruido |
| 5 | Victoria / logro | Fanfarria ascendente + armonia |

Si el paquete trae **`E:1`**, el cliente ignora `S:` y reproduce un **pitido de rechazo** (tambien en fallos de red/archivo).

### 10.2 Paquete hacia el CPC

```text
T:linea1|linea2|linea3
S:2
E:0
I:+objeto
L:lugar
F:clave=1
```

- `T:` narracion (solo esto lee el jugador en el Amstrad)
- `S:` sonido 0-5 · `E:0` ok / `E:1` error
- `I:` / `L:` / `F:` solo en el PC (inventario, lugar, flags)
- Cada etiqueta en **linea propia**; nunca unir con `/`
- Fin de linea **CRLF**
- Esquema detallado: [ESQUEMA_PAQUETE.md](ESQUEMA_PAQUETE.md)

### 10.3 Estado de partida (PC)

- **Lugar** (`L:`)
- **Inventario** (`I:+obj` / `I:-obj` / lista)
- **Flags** (`F:clave=1`)

Visibles en el panel; consultables en CPC con `INV` (inventario).

---

## 11. Guardar y cargar partidas

- **Donde se guardan:** ficheros JSON en `server/saves/slot1.json` … `slot3.json` (en el PC).
- **Que se guarda:**
  - **Mundo:** prompt `system` + `start_state` (la aventura generada / en juego)
  - **Situacion:** lugar, inventario, flags
  - **Conversacion:** historial reciente (~10 turnos / 20 mensajes user+assistant)
  - **Memoria de trama (`plot_summary`):** hechos que salen de la ventana de historial; se reinyectan al LLM en cada turno para no “olvidar” la historia
- **LOAD:** restaura todo eso **en memoria** y envia al CPC un **resumen de reanudacion**: mundo (titulo/premisa), situacion (lugar, inventario, hechos), y un recuerdo de la ultima accion / narracion. **No** reescribe `settings.json`.
- **Slots antiguos** (sin `system` / sin `plot_summary`): cargan lo que haya; el prompt en memoria no cambia si falta mundo; el CPC avisa `Mundo no embebido` si aplica.
- **Desde CPC:** `SAVE 2`, `LOAD 2`, `SAVES` (f3/f4 = slot 1).
- **Desde panel:** bloque Partidas → elegir slot → Guardar / Cargar.

Si cargas un slot vacio: mensaje de error (`E:1`).

---

## 12. Problemas frecuentes

| Sintoma | Que revisar |
|---------|-------------|
| Intro: SERVIDOR NO ACTIVO | `run_server.bat` en marcha; `P$` = IP del PC; firewall 8080; misma Wi‑Fi |
| `Fallo red/archivo` | M4 conectada (`|NETSTAT`); servidor en `0.0.0.0:8080` |
| Texto cortado o `...` | Limite 12×40 del protocolo; normal si la IA escribe de mas |
| Texto basura / ERROR: raro | Servidor antiguo sin CRLF; actualiza y reinicia `server.py` |
| `Sin conexion con el servidor.` tras un turno | Fallo de red o `RESP.TXT` vacio: se vacia el fichero antes del GET para no repetir el turno anterior. `R` reenvia; espacio vuelve al prompt |
| IA no responde | Proveedor/key correctos; panel en modo IA; mira **Error LLM** (OpenRouter a veces `content` vacio: el panel muestra error, no crash) |
| Siempre arranca en Ollama | Pulsa **Guardar** tras elegir proveedor; comprueba que existe `server/settings.json` |
| Mock siempre igual | Es normal sin palabras clave; cambia a modo IA |
| `RUN"aventura` no carga | Guarda desde emulador (`SAVE`) o sube por web UI M4; CRLF en ASCII |
| `(Sin T2.SCR…)` / titulo MODE 2 ausente | `T2.SCR` en la misma carpeta; debe llevar cabecera AMSDOS (`make_title2_scr.py`) |
| Sin titulo MODE 1 | Falta `TITLE.SCR` junto al `.bas`; el juego continua |
| Load no restaura en CPC | El load afecta al **servidor**; el siguiente turno en CPC ya usa ese estado |
| Panel no responde / congelado | Reinicia `server.py` |
| Selector modelos vacio (Ollama) | Ollama debe estar arriba; pulsa **Modelos ↺**; mira consola del servidor |
| Selector modelos vacio (cloud) | Introduce la API key → espera 1 s → se cargan solos; o pulsa **Modelos ↺** |

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
| Manifest / iconos panel | `server/web/manifest.webmanifest`, `icon-*.png` |
| Icono fuente | `imagen/icon.png` |
| Launcher CPC | `client/sintaxia.bas` |
| Cliente CPC MODE 1 | `client/aventura.bas` |
| Cliente CPC MODE 2 | `client/aventuramode2.bas` |
| Titulo MODE 1 | `client/TITLE.SCR` (manual; no pisar) |
| Titulo MODE 2 | `client/T2.SCR` (+ alias `TITLE2.SCR`) |
| Generar titulo MODE 2 | `tools/make_title2_scr.py` (+ `tools/amsdos_header.py`) |
| Cabecera AMSDOS | `tools/amsdos_header.py` |
| Arranque PC | `run_server.bat` |
| Ajustes locales | `server/settings.json` (gitignored) |
| Esquema paquete | `docs/ESQUEMA_PAQUETE.md` |
| Guia jugador | `docs/GUIA_JUGADOR.md` |
| Notas cortas SD | `docs/CARGA.md` |
| Handoff tecnico | `docs/SINTAXIA_HANDOFF.md` |
| Hardware M4 | https://github.com/M4Duke/m4hardware |
| Codigo | https://github.com/kapi21/SINTAXIA |

---

*Fin del manual. Que la antorcha no se apague.*
