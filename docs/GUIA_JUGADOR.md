# SINTAXIA — Guia rapida para jugar

Bienvenido a **SINTAXIA**: una aventura de texto en tu Amstrad CPC, donde un maestro (inteligencia artificial en el PC) inventa la historia contigo.

No hace falta saber programar. Solo necesitas el CPC con la tarjeta M4, un PC en la misma Wi‑Fi y seguir estos pasos.

---

## Que vas a vivir

Escribes lo que quieres hacer, como si hablaras con alguien:

> miro alrededor  
> abro la puerta  
> cojo la antorcha  

El maestro te responde con la narracion de forma **animada letra a letra** (efecto maquina de escribir) acompanado de sonido sinteticos en el chip del Amstrad. 

Ademas:
- **Colores dinamicos**: El texto cambia de color segun el momento (ambar para historia, rojo para peligro/combate, verde para tesoros y logros).
- **El borde cambia de color** segun la situacion.
- **Paginacion**: Si la historia es larga, el juego se pausa con `[ESPACIO para continuar]` para que no te pierdas nada.

Tambien puedes guardar la partida y retomarla otro dia.

---

## Lo que necesitas

1. **Amstrad CPC** con **M4 Board** ya conectada a tu Wi‑Fi.  
2. **PC** (Windows) en la **misma Wi‑Fi**, con el programa SINTAXIA y, si puedes, Ollama instalado (para la IA).  
3. El fichero del juego en la tarjeta de la M4: `aventura.bas`.

Si alguien te ha dejado el sistema preparado, salta a [Empezar a jugar](#empezar-a-jugar).

---

## Preparar el PC (una vez)

1. Enciende el PC y conectalo a la Wi‑Fi de casa.  
2. Abre la carpeta de SINTAXIA.  
3. Haz doble clic en **`run_server.bat`**.  
   - Deja esa ventana abierta mientras juegas.  
4. (Opcional) Abre el navegador en:  
   **http://127.0.0.1:8080/ui**  
   Ahi veras un panel con pinta de Amstrad. Deja **Modo = IA** si quieres la aventura con inteligencia artificial.  
   Si pasas el raton por el **?** junto a cada opcion, aparece una ventanita explicando que hace.  
   Puedes elegir **Ollama** (local) o APIs de **OpenAI**, **Claude** o **Gemini** (necesitas su clave).

Si no tienes IA instalada, en el panel puedes poner **Modo = Mock**: el juego responde de forma sencilla para probar que todo conecta.

---

## Preparar el Amstrad (una vez)

1. Enciende el CPC con la M4 y la microSD.  
2. Escribe: `|NETSTAT`  
   Debe mostrar que hay red e IP.  
3. Si te han dicho que cambies la IP del PC en el juego, pide ayuda a quien te lo instalo (esta al principio del programa `aventura.bas`).  
4. Arranca el juego:  
   `RUN"aventura`  
   (Copia tambien `TITLE.SCR` a la microSD si quieres la pantalla grafica de titulo.)

---

## Empezar a jugar

1. PC: `run_server.bat` en marcha.  
2. CPC: `RUN"aventura`  
3. Si aparece el titulo (castillo/puerta), pulsa **ESPACIO**.  
4. En la pantalla de inicio deberia salir algo como **SERVIDOR ACTIVO**.  
5. Escribe, por ejemplo:  
   `miro alrededor`  
6. Espera un momento (“Esperando al maestro…”) y lee la respuesta.

Si sale **SERVIDOR NO ACTIVO**:

- Mira que el PC tenga el programa abierto.  
- Pulsa **R** en el CPC para reintentar.  
- Comprueba que ambos estan en la misma Wi‑Fi.

---

## Como se juega

- Escribe **acciones en español normal**. No hace falta memorizar verbos raros.  
- Cuanto mas claro digas lo que haces, mejor te entiende el maestro.  
- Puedes explorar, coger objetos, hablar, pelear, resolver situaciones… segun lo que narre la historia.  
- El juego lleva un **inventario** (lo que llevas encima).

### Comandos utiles

| Escribes | Que pasa |
|----------|----------|
| `AYUDA` | Te recuerda los comandos. |
| `INV` | Mira lo que llevas encima. |
| `!` | Repite el ultimo comando que escribiste. |
| `D` | Pantalla de diagnostico (revisa tu conexion y estado del juego). |
| `NUEVA` | Empieza una aventura desde cero. |
| `SAVE 1` | Guarda la partida en la ranura 1 (tambien 2 o 3). |
| `LOAD 1` | Carga la partida de esa ranura. |
| `SAVES` | Te dice que ranuras tienes ocupadas. |
| `QUIT` | Sales del juego. |

Ejemplos de acciones (no son comandos fijos; inventa las tuyas):

```text
miro alrededor
voy al norte
abro el cofre
hablo con la figura
uso la llave
```

---

## Guardar y seguir otro dia

1. Cuando quieras parar: `SAVE 1` (o 2, o 3).  
2. Apaga con `QUIT` si quieres.  
3. Otro dia: enciende PC (`run_server.bat`), CPC (`RUN"aventura`) y escribe `LOAD 1`.

Tambien puedes guardar y cargar desde el panel del PC (pantalla bonita del navegador), eligiendo la ranura 1, 2 o 3.

---

## Panel del PC (opcional, facil)

Direccion: **http://127.0.0.1:8080/ui**

Para un jugador normal basta con:

- Ver que pone **READY** / servidor activo.  
- Dejar **Modo = IA** (o Mock para pruebas).  
- Usar **Nueva** si quieres reiniciar la historia.  
- Usar **Guardar / Cargar** de partidas si te resulta mas comodo que en el CPC.

El resto de opciones (modelo, temperatura, etc.) son para quien administra el sistema; no hace falta tocarlas para disfrutar.

---

## Si algo falla

| Que ves | Que probar |
|---------|------------|
| No encuentra el servidor | PC con `run_server.bat` abierto; misma Wi‑Fi; tecla **R** en la intro. |
| Se queda mucho en “Esperando…” | La IA tarda un poco la primera vez; espera. Si no responde, revisa el panel del PC. |
| El texto se corta con `...` | Es normal: el Amstrad muestra textos cortos. |
| No carga `RUN"aventura` | Pide a quien te ayudo que deje el fichero bien guardado en la tarjeta. |

---

## Resumen en 30 segundos

1. PC: doble clic en `run_server.bat`.  
2. CPC: `RUN"aventura`.  
3. Escribe lo que haces.  
4. `SAVE 1` para guardar.  
5. `QUIT` para salir.

**Disfruta la aventura.** Que la antorcha no se apague.
