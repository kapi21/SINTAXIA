## SINTAXIA — Demo Version 1.1

Mejora la **coherencia de la historia** y la **primera configuracion**. Sustituye a la Demo v1.

### Novedades
- **Asistente de configuracion** obligatorio en `/ui` la primera vez (proveedor, modelo, clave) y opcion de reconfigurar.
- **Memoria de trama:** historial ampliado (~10 turnos) y resumen automatico de los hechos antiguos, guardado tambien en las partidas.
- Correcciones en el cliente `aventura.bas` (MODE 1).

### Que incluye el ZIP
- **01_PC/** servidor Python + panel web (`run_server.bat`)
- **02_microSD/** ficheros para la tarjeta (misma carpeta)
- **03_docs/** guia del jugador, manual y carga

### Requisitos
CPC con **M4 Board**, PC con **Python 3.10+**, Ollama / API (OpenRouter, OpenAI, Claude, Gemini...) o modo Mock, firewall TCP **8080**.

### Arranque rapido
1. PC: `01_PC/run_server.bat` → http://127.0.0.1:8080/ui y sigue el asistente
2. SD: copia `02_microSD` y crea `HOST.TXT` con `IP:8080` del PC
3. CPC: `|NETSTAT` → `RUN"sintaxia` → 1 o 2

Articulo en AUA: https://auamstrad.es/software/sintaxia-una-aventura-conversacional-con-ia/
Licencia MIT. Sigue siendo una demo; feedback bienvenido.
