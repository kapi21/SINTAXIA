# SINTAXIA — Guia rapida para jugar

Bienvenido a **SINTAXIA**: una aventura de texto en tu Amstrad CPC, donde un maestro (inteligencia artificial en el PC) inventa la historia contigo.

No hace falta saber programar. Solo necesitas el CPC con la tarjeta M4, un PC en la misma Wi‑Fi y seguir estos pasos.

---

## Que vas a vivir

Escribes lo que quieres hacer, como si hablaras con alguien:

> miro alrededor  
> abro la puerta  
> cojo la antorcha  

El maestro te responde con narracion **letra a letra** (maquina de escribir) y sonidos del chip del Amstrad.

Ademas:

- **Colores dinamicos** segun el momento (historia, peligro, tesoro…).
- **El borde cambia** segun la situacion.
- Al empezar (y con `NUEVA`) lees un **resumen de situacion**: donde estas y que ocurre, sin tecnicismos.
- Puedes **guardar** la partida y retomarla otro dia.

---

## Lo que necesitas

1. **Amstrad CPC** con **M4 Board** en tu Wi‑Fi.  
2. **PC** (Windows) en la **misma Wi‑Fi**, con SINTAXIA y una IA (Ollama local, OpenRouter u otra API).  
3. En la microSD: `aventura.bas` y, si puedes, `TITLE.SCR` (pantalla de titulo).

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
3. Si hay que cambiar la IP del PC, esta al inicio de `aventura.bas` (`P$`).  
4. `RUN"aventura`  
   (Con `TITLE.SCR` en la misma carpeta veras el titulo grafico.)

---

## Empezar a jugar

1. PC: `run_server.bat` en marcha.  
2. CPC: `RUN"aventura`  
3. Si hay titulo grafico (con un jingle corto), pulsa **ESPACIO**.  
4. Lee la pantalla de ayuda y pulsa **ESPACIO** otra vez para comprobar el servidor.  
5. Debe salir **SERVIDOR ACTIVO** y luego **Situacion** (resumen completo del mundo; si es largo, pulsa **ESPACIO** entre paginas).  
6. Escribe, por ejemplo: `miro alrededor`  
7. Espera (“Pensando…” con spinner) y lee la respuesta.

Si sale **SERVIDOR NO ACTIVO**: PC con el programa abierto, misma Wi‑Fi, tecla **R** para reintentar.

---

## Como se juega

- Acciones en **espanol normal**.  
- Frases claras ayudan al maestro.  
- Hay **inventario** (lo que llevas).

### Comandos utiles

| Escribes | Que pasa |
|----------|----------|
| `AYUDA` | Recuerda comandos. |
| `INV` | Mira lo que llevas. |
| `!` | Repite el ultimo comando. |
| `D` | Diagnostico (conexion / estado). |
| `NUEVA` o `REINICIO` | Empieza de cero con el mundo que hay ahora en el PC (y vuelve a contar la situacion). |
| `SAVE 1` | Guarda en ranura 1 (tambien 2 o 3). |
| `LOAD 1` | Carga esa ranura. |
| `SAVES` | Lista ranuras. |
| `QUIT` | Guarda en slot 1 y reinicia el CPC. |

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
