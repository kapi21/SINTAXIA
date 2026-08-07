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
- **Borde negro** fijo.
- Al empezar (y con `NUEVA`) lees un **resumen de situacion**: donde estas y que ocurre.
- Puedes **guardar** la partida y retomarla con `LOAD`.
- Al arrancar veras **Iniciando la aventura...** (y en el launcher, el modo elegido) para saber que esta cargando.
- Atajos **F1**–**F9**; flechas = historial; `!` = ultimo. **NUEVA** y **QUIT** piden **S/N**.

Hay **un launcher** y **dos clientes** en la microSD:

| Fichero | Rol | Notas |
|---------|-----|--------|
| `sintaxia.bas` | Launcher | Elige MODE 1 o 2 (aviso al seleccionar) |
| `aventura.bas` | MODE 1 (40 cols) | Titulo grafico `TITLE.SCR` si esta en la SD |
| `aventuramode2.bas` | MODE 2 (80 cols) | Negro/verde; titulo `T2.SCR` (o `TITLE2.SCR`) |
| `T2.SCR` | Titulo MODE 2 | Misma carpeta que el `.bas` (con cabecera AMSDOS) |
| `TITLE.SCR` | Titulo MODE 1 | Misma carpeta que el `.bas` |
| `ver_title2.bas` | Prueba | Solo para ver el titulo MODE 2 |

---

## Lo que necesitas

1. **Amstrad CPC** con **M4 Board** en tu Wi‑Fi.  
2. **PC** (Windows) en la **misma Wi‑Fi**, con SINTAXIA y una IA (Ollama, OpenRouter u otra).  
3. En la **microSD**, **todos en la misma carpeta** (no hace falta ninguna carpeta `client/` en la tarjeta):

```text
sintaxia.bas
aventura.bas
aventuramode2.bas
TITLE.SCR
T2.SCR
```

(Opcional: `TITLE2.SCR` = copia de `T2.SCR`; `HOST.TXT` con la IP del PC; `ver_title2.bas` para probar el titulo.)

Si alguien te lo dejo preparado, salta a [Empezar a jugar](#empezar-a-jugar).

---

## Preparar el PC (una vez)

1. Enciende el PC y conectalo a la Wi‑Fi.  
2. Abre la carpeta de SINTAXIA.  
3. Doble clic en **`run_server.bat`**. Deja esa ventana abierta.  
4. Panel: **http://127.0.0.1:8080/ui**  
   - **Modo = IA**; elige proveedor/modelo; **Guardar**.  
   - **Movil (misma Wi‑Fi):** `http://IP-DEL-PC:8080/ui` → Anadir a pantalla de inicio.

Sin IA: **Modo = Mock** para probar la red.

---

## Preparar el Amstrad (una vez)

1. Enciende el CPC con la M4 y la microSD.  
2. `|NETSTAT` — debe haber red e IP.  
3. Si hay que cambiar la IP del PC: **F7** / `IP` (guarda `HOST.TXT`).  
4. `RUN"sintaxia` — **1** = MODE 1, **2** = MODE 2  
   (o `RUN"aventura` / `RUN"aventuramode2` en directo.)

---

## Empezar a jugar

1. PC: `run_server.bat` en marcha.  
2. CPC: `RUN"sintaxia` → **1** o **2** (veras “Seleccionado Modo… / Iniciando…”).  
3. Titulo grafico + musica → **ESPACIO** cuando quieras seguir.  
4. Pantalla de bienvenida → **ESPACIO** para comprobar el servidor.  
5. **SERVIDOR ACTIVO** y **Situacion** (si es larga, **ESPACIO** entre paginas).  
6. Escribe, por ejemplo: `miro alrededor`.  
7. “Pensando…” → lee la respuesta. Una tecla acelera el typewriter; **F9** = texto rapido permanente.

Si sale **SERVIDOR NO ACTIVO**: misma Wi‑Fi, tecla **R** para reintentar.

---

## Como se juega

- Acciones en **espanol normal**.  
- Frases claras ayudan al maestro.  
- Hay **inventario** (lo que llevas).

### Comandos utiles

| Escribes | Que pasa |
|----------|----------|
| `AYUDA` o **F2** | Lista de comandos **debajo** del texto (no borra la pantalla). |
| `INV` o **F1** | Mira lo que llevas. |
| `SAVE 1` o **F3** | Guarda en ranura 1. |
| `LOAD 1` o **F4** | Carga ranura 1. |
| `!` o **flechas ARR/ABJ** | Historial (hasta 5). |
| `D` | Diagnostico. |
| `NUEVA` / **F5** | Nueva partida (**S/N**). |
| `SONIDO` / **F6** | Sonido ON/OFF. |
| `MUTE` / `SILENCIO` | Apaga el AY. |
| `IP` / **F7** | Cambia IP:puerto del PC. |
| `RAPIDO` / **F9** | Texto rapido persistente. |
| `LENTO` | Typewriter letra a letra. |
| `SAVE 2` / `SAVE 3` | Otras ranuras. |
| `LOAD 2` / `LOAD 3` | Carga esas ranuras. |
| `SAVES` | Lista ranuras. |
| `QUIT` o **F8** | Salir (**S/N**); vuelve a la bienvenida. |

Durante la narracion, **cualquier tecla** acelera; **ESPACIO** pagina si el turno es largo.

---

## Guardar y seguir otro dia

1. `SAVE 1` (o 2 / 3).  
2. `QUIT` / **F8** si quieres salir (no guarda solo; usa `SAVE` antes).  
3. Otro dia: `run_server.bat` + `RUN"sintaxia` + `LOAD 1`.

Tambien desde el panel del PC (slots).

---

## Panel del PC (opcional)

**http://127.0.0.1:8080/ui**

- **READY**, **Modo = IA** (o Mock), **Nueva**, Guardar/Cargar slots.  
- Avanzado: Generar prompt, modelo, API key; **Guardar** para el proximo arranque.

---

## Si algo falla

| Que ves | Que probar |
|---------|------------|
| No encuentra el servidor | `run_server.bat`; misma Wi‑Fi; **R** en la intro. |
| Tarda en “Pensando…” | La IA puede tardar; mira el panel. |
| El texto acaba en `...` | Limite de 12 lineas; normal a veces. |
| No carga `RUN"sintaxia"` | Ficheros en la SD; ASCII con CRLF. |
| `(Sin T2.SCR…)` / sin titulo MODE 2 | Copia `T2.SCR` (con cabecera) **junto** al `.bas`; prueba `RUN"ver_title2`. |
| Sin titulo MODE 1 | Falta `TITLE.SCR` en la misma carpeta; el juego sigue. |

---

## Resumen en 30 segundos

1. PC: `run_server.bat`.  
2. CPC: `RUN"sintaxia` → **1** o **2** → ESPACIO en titulo.  
3. Lee la **Situacion** y escribe lo que haces.  
4. `SAVE 1` para guardar; `QUIT` / **F8** para la bienvenida.

**Disfruta la aventura.**
