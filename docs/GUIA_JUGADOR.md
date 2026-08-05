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
- Puedes **guardar** la partida y retomarla otro dia.
- Atajos: **f1** inventario, **f2** ayuda, **f3** guardar slot 1, **f4** cargar slot 1, **f5** nueva partida, **f6** alternar sonido; **flechas arriba/abajo** recorren el historial (hasta 5); `!` repite el ultimo. **NUEVA** y **QUIT** piden confirmacion **S/N**. `MUTE`/`SILENCIO` apagan el AY; `SONIDO` lo enciende; `AUDIO` alterna.

Hay **dos clientes** en la microSD:

| Fichero | Modo | Notas |
|---------|------|--------|
| `aventura.bas` | MODE 1 (40 cols) | Oficial; usa `TITLE.SCR` si esta en la SD |
| `aventuramode2.bas` | MODE 2 (80 cols) | Negro/verde; mas texto por linea; sin `TITLE.SCR` |

---

## Lo que necesitas

1. **Amstrad CPC** con **M4 Board** en tu Wi‑Fi.  
2. **PC** (Windows) en la **misma Wi‑Fi**, con SINTAXIA y una IA (Ollama local, OpenRouter u otra API).  
3. En la microSD: `aventura.bas` (MODE 1) y, si quieres, `aventuramode2.bas` (MODE 2) y `TITLE.SCR` (solo MODE 1).

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

Sin IA: **Modo = Mock** para probar que la red funciona.

---

## Preparar el Amstrad (una vez)

1. Enciende el CPC con la M4 y la microSD.  
2. `|NETSTAT` — debe haber red e IP.  
3. Si hay que cambiar la IP del PC, esta al inicio de `aventura.bas` o `aventuramode2.bas` (`P$`).  
4. `RUN"aventura`   — MODE 1  
   o `RUN"aventuramode2` — MODE 2 (80 columnas)  
   (Con `TITLE.SCR` junto a `aventura.bas` veras el titulo grafico en MODE 1.)

---

## Empezar a jugar

1. PC: `run_server.bat` en marcha.  
2. CPC: `RUN"aventura` o `RUN"aventuramode2`  
3. En MODE 1, si hay titulo grafico, suena un **tema de intro** corto; pulsa **ESPACIO** (corta la musica). En MODE 2 hay splash de texto.  
4. Lee la pantalla de ayuda y pulsa **ESPACIO** otra vez para comprobar el servidor.  
5. Debe salir **SERVIDOR ACTIVO** y luego **Situacion** (resumen completo del mundo; si es largo, pulsa **ESPACIO** entre paginas).  
6. Escribe, por ejemplo: `miro alrededor` (DEL borra; **f1**–**f6** atajos; flechas = historial).  
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
| `AYUDA` o **f2** | Recuerda comandos. |
| `INV` o **f1** | Mira lo que llevas. |
| `SAVE 1` o **f3** | Guarda en ranura 1. |
| `LOAD 1` o **f4** | Carga ranura 1. |
| `!` o **flechas ARR/ABJ** | Historial de hasta 5 comandos (`!` = el ultimo). |
| `D` | Diagnostico (conexion / estado). |
| `NUEVA` / `REINICIO` o **f5** | Nueva partida (pide **S/N**). |
| `MUTE` / `SILENCIO` | Apaga efectos AY. |
| `SONIDO` | Enciende efectos AY. |
| `AUDIO` o **f6** | Alterna sonido on/off. |
| `SAVE 2` / `SAVE 3` | Otras ranuras. |
| `LOAD 2` / `LOAD 3` | Carga esas ranuras. |
| `SAVES` | Lista ranuras. |
| `QUIT` | Salir (pide **S/N**; guarda slot 1 y reinicia CPC). |

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

1. `SAVE 1` (o 2 / 3).  
2. `QUIT` si quieres apagar.  
3. Otro dia: PC (`run_server.bat`) + CPC (`RUN"aventura`) + `LOAD 1`.

Tambien desde el panel del PC (Guardar / Cargar slots).

---

## Panel del PC (opcional)

**http://127.0.0.1:8080/ui**

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
| No carga `RUN"aventura"` | Fichero bien en la SD (a veces hace falta tokenizar el `.bas`). |
| Sin titulo grafico | Falta `TITLE.SCR` o fallo de carga; el juego sigue igual. |

---

## Resumen en 30 segundos

1. PC: `run_server.bat`.  
2. CPC: `RUN"aventura` → ESPACIO en titulo → ESPACIO en ayuda.  
3. Lee la **Situacion** (ESPACIO si pide mas paginas) y escribe lo que haces.  
4. `SAVE 1` para guardar; `NUEVA` para empezar de cero.  
5. `QUIT` para salir.

**Disfruta la aventura.**
