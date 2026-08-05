# SINTAXIA — Guia rapida para jugar

Bienvenido a **SINTAXIA**: una aventura de texto en tu Amstrad CPC, donde un maestro (inteligencia artificial en el PC) inventa la historia contigo.

No hace falta saber programar. Solo necesitas el CPC con la tarjeta M4, un PC en la misma Wi‑Fi y seguir estos pasos.

---

## Que vas a vivir

Escribes lo que quieres hacer, como si hablaras con alguien:

> miro alrededor  
> abro la puerta  
> cojo la antorcha  

El maestro te responde con narracion **letra a letra** (maquina de escribir) y sonidos del chip del Amstrad. Si quieres leer mas rapido, pulsa **cualquier tecla** y el texto se vuelca de golpe.

Ademas:

- **Colores de texto** en MODE 1 segun el momento (historia, peligro, tesoro…).
- **Borde negro** fijo (sin flashes de color).
- Al empezar (y con `NUEVA`) lees un **resumen de situacion**: donde estas y que ocurre, sin tecnicismos.
- Puedes **guardar** la partida (mundo + situacion + conversacion reciente) y retomarla otro dia con `LOAD`.
- Atajos: **F1**–**F8** (INV, AYUDA, SAVE/LOAD 1, NUEVA, SONIDO ON/OFF, IP, QUIT); **flechas** = historial; `!` = ultimo. **NUEVA** y **QUIT** piden **S/N**. `MUTE` silencia. La IP del PC se puede cambiar con **F7** (se guarda en `HOST.TXT` en la SD).

Hay **un launcher** y **dos clientes** en la microSD:

| Fichero | Rol | Notas |
|---------|-----|--------|
| `sintaxia.bas` | Launcher | Entrada recomendada: elige MODE 1 o 2 |
| `aventura.bas` | MODE 1 (40 cols) | Oficial; usa `TITLE.SCR` si esta en la SD |
| `aventuramode2.bas` | MODE 2 (80 cols) | Negro/verde; mas texto por linea; sin `TITLE.SCR` |

---

## Lo que necesitas

1. **Amstrad CPC** con **M4 Board** en tu Wi‑Fi.  
2. **PC** (Windows) en la **misma Wi‑Fi**, con SINTAXIA y una IA (Ollama local, OpenRouter u otra API).  
3. En la microSD: `sintaxia.bas`, `aventura.bas`, `aventuramode2.bas` y `TITLE.SCR` (solo MODE 1).

Si alguien te lo dejo preparado, salta a [Empezar a jugar](#empezar-a-jugar).

---

## Preparar el PC (una vez)

1. Enciende el PC y conectalo a la Wi‑Fi.  
2. Abre la carpeta de SINTAXIA.  
3. Doble clic en **`run_server.bat`**.  
   - Deja esa ventana abierta.  
   - Suele abrirse solo el panel en el navegador.  
4. Panel: **http://127.0.0.1:8080/ui**  
   - **Modo = IA** para jugar con inteligencia artificial.  
   - Puedes elegir Ollama, OpenAI, Claude, Gemini u **OpenRouter** (con su clave).  
   - Pulsa **Guardar**: el PC recuerda proveedor, modelo y clave para el proximo arranque.  
   - Pasa el raton por el **?** de cada opcion para ver ayuda.  
   - Quien administra el sistema puede pulsar **Generar prompt** para inventar un mundo nuevo y luego **Guardar**.  
   - **Movil (misma Wi‑Fi):** abre `http://IP-DEL-PC:8080/ui` → menu del navegador → **Anadir a pantalla de inicio** (icono SINTAXIA).

Sin IA: **Modo = Mock** para probar que la red funciona.

---

## Preparar el Amstrad (una vez)

1. Enciende el CPC con la M4 y la microSD.  
2. `|NETSTAT` — debe haber red e IP.  
3. Si hay que cambiar la IP del PC: **F7** / `IP` (guarda `HOST.TXT`), o edita `P$` al inicio del `.bas`.
4. `RUN"sintaxia` — menu: **1** = MODE 1, **2** = MODE 2  
   (Tambien puedes `RUN"aventura` o `RUN"aventuramode2` en directo.)  
   (Con `TITLE.SCR` junto a `aventura.bas` veras el titulo grafico en MODE 1.)

---

## Empezar a jugar

1. PC: `run_server.bat` en marcha.  
2. CPC: `RUN"sintaxia` → pulsa **1** o **2**  
   (o `RUN"aventura` / `RUN"aventuramode2` en directo)  
3. En MODE 1/2, al titulo suena un **tema de intro** (~2 min, se repite); pulsa **ESPACIO** cuando quieras seguir (corta la musica).
4. Lee la pantalla de ayuda y pulsa **ESPACIO** otra vez para comprobar el servidor.  
5. Debe salir **SERVIDOR ACTIVO** y luego **Situacion** (resumen completo del mundo; si es largo, pulsa **ESPACIO** entre paginas).  
6. Escribe, por ejemplo: `miro alrededor` (DEL borra; **F1**–**F8** atajos; flechas = historial).  
7. Espera (“Pensando…” con spinner) y lee la respuesta. Una tecla salta el typewriter.

Si sale **SERVIDOR NO ACTIVO**: PC con el programa abierto, misma Wi‑Fi, tecla **R** para reintentar.

---

## Como se juega

- Acciones en **espanol normal**.  
- Frases claras ayudan al maestro.  
- Hay **inventario** (lo que llevas).

### Comandos utiles

| Escribes | Que pasa |
|----------|----------|
| `AYUDA` o **F2** | Recuerda comandos. |
| `INV` o **F1** | Mira lo que llevas. |
| `SAVE 1` o **F3** | Guarda en ranura 1. |
| `LOAD 1` o **F4** | Carga ranura 1. |
| `!` o **flechas ARR/ABJ** | Historial de hasta 5 comandos (`!` = el ultimo). |
| `D` | Diagnostico (conexion / estado). |
| `NUEVA` / `REINICIO` o **F5** | Nueva partida (pide **S/N**). |
| `SONIDO` / **F6** | Alterna sonido ON/OFF. |
| `MUTE` / `SILENCIO` | Apaga el AY. |
| `IP` / `HOST` / **F7** | Cambia IP:puerto del PC (guarda `HOST.TXT`). |
| `AUDIO` | Igual que SONIDO (toggle). |
| `SAVE 2` / `SAVE 3` | Otras ranuras. |
| `LOAD 2` / `LOAD 3` | Carga esas ranuras. |
| `SAVES` | Lista ranuras. |
| `QUIT` o **F8** | Salir sin guardar (pide **S/N**); vuelve a la pantalla de bienvenida. |

Durante la narracion, **cualquier tecla** acelera el texto.

Ejemplos de acciones:

```text
miro alrededor
voy al norte
abro el cofre
hablo con la figura
uso la llave
```

---

## Guardar y seguir otro dia

1. `SAVE 1` (o 2 / 3) — guarda el **mundo**, donde estas, inventario y la charla reciente.  
2. `QUIT` / **F8** — «Salir sin guardar?»; vuelve a la bienvenida (no guarda solo; usa `SAVE` antes si quieres).  
3. Otro dia: PC (`run_server.bat`) + CPC (`RUN"sintaxia`) + `LOAD 1` — te reubicara en el mundo, la situacion y un recuerdo de lo ultimo que hiciste.

Tambien desde el panel del PC (Guardar / Cargar slots).

---

## Panel del PC (opcional)

**http://127.0.0.1:8080/ui** (en movil: `http://IP-DEL-PC:8080/ui` → **Anadir a pantalla de inicio**)

Para jugar basta con:

- Ver **READY**.  
- **Modo = IA** (o Mock).  
- **Nueva** en el panel si quieres reiniciar en el PC.  
- Guardar / Cargar slots.

Opciones avanzadas (quien monta el sistema):

- **Generar prompt**: inventa un mundo nuevo (luego **Guardar**).  
- **Prompt por defecto**: vuelve al castillo clasico (luego **Guardar**).  
- Modelo, temperatura, API key (OpenRouter u otras).  
- Tras **Guardar**, esos ajustes se reutilizan al volver a abrir `run_server.bat`.

---

## Si algo falla

| Que ves | Que probar |
|---------|------------|
| No encuentra el servidor | `run_server.bat` abierto; misma Wi‑Fi; **R** en la intro. |
| Tarda en “Pensando…” / situacion | La IA puede tardar; espera. Revisa el panel. |
| El texto acaba en `...` | Solo si la IA se pasa de 12 lineas; suele bastar. |
| No carga `RUN"sintaxia"` | Fichero bien en la SD (a veces hace falta tokenizar el `.bas`). |
| Sin titulo grafico | Falta `TITLE.SCR` o fallo de carga; el juego sigue igual. |

---

## Resumen en 30 segundos

1. PC: `run_server.bat`.  
2. CPC: `RUN"sintaxia` → **1** o **2** → ESPACIO en titulo/ayuda.  
3. Lee la **Situacion** (ESPACIO si pide mas paginas) y escribe lo que haces.  
4. `SAVE 1` para guardar; `NUEVA` para empezar de cero.  
5. `QUIT` / **F8** para volver a la bienvenida (sin guardar automatico).

**Disfruta la aventura.**
