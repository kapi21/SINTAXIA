# Cargar aventura.bas en el CPC (Fase 2/3)

## Requisitos
- Servidor en el PC: `run_server.bat` o `cd server` + `python server.py` (puerto 8080)
- M4 en red (ahora `192.168.1.128`)
- PC en `192.168.1.4`

## Firewall (PC, una vez)
Permitir TCP 8080 entrante, o prueba temporal:
```powershell
New-NetFirewallRule -DisplayName "Aventura CPC 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

## Probar servidor desde el PC
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8080/ping" -UseBasicParsing
Invoke-WebRequest -Uri "http://192.168.1.4:8080/turn?msg=miro+la+cueva" -UseBasicParsing
```

## Pasar el BASIC a la microSD
1. Copia a la microSD de la M4:
   - `client/sintaxia.bas` (launcher)
   - `client/aventura.bas`
   - `client/aventuramode2.bas` (si usas MODE 2)
   - `client/TITLE.SCR` (titulo MODE 1; opcional pero recomendado)
   - `client/T2.SCR` (titulo MODE 2; **misma carpeta** que `aventuramode2.bas`)
   - `client/TITLE2.SCR` (alias opcional; el cliente tambien lo prueba)
2. Formato: **ASCII** (Locomotive). Misma copia en `client/ascii/` por si editas aparte.
   - Si `RUN"sintaxia` no carga en algun entorno raro: abre WinAPE/CPCemu, carga el listado y `SAVE"sintaxia` (tokenizado nativo del CPC).
   - El tokenizador casero esta **aparcado** en `archivo/tokenizado_cpc/` (no usar en SD).
3. Alternativa M4 Web UI: `http://192.168.1.128` → subir fichero.

### Regenerar TITLE.SCR / T2.SCR (PC)
```powershell
python tools/make_title_scr.py
python tools/make_title2_scr.py
```
Genera dumps con **cabecera AMSDOS** (necesarios para `LOAD` en la M4).  
En la SD van en la **misma carpeta** que el `.bas` (nombres `TITLE.SCR` / `T2.SCR`).  
La ruta `client/` es solo del PC al copiar; el BASIC hace `LOAD"T2.SCR",&C000` **sin** carpeta.

## En el CPC
```
|NETSTAT
RUN"sintaxia
```
Pulsa **1** (MODE 1) o **2** (MODE 2).  
En MODE 1: primero el titulo grafico (jingle) → **ESPACIO**. Luego ayuda → **ESPACIO**, ping, y el resumen **MUNDO** completo (si es largo, **ESPACIO** entre paginas).  
Si al cargar el `.bas` sale **Overflow**, revisa que no haya numeros de linea >32767.  
Prueba mensajes: `miro la cueva`, `cojo la espada`, `atacar`, `tesoro`, `QUIT`

## Si falla la red
- Confirma el servidor en el PC (`run_server.bat`)
- Desde CPC: `|HTTPGET,"192.168.1.4:8080/ping>PING.TXT"`. En BASIC:
```
|HTTPGET,"@192.168.1.4:8080/ping>PING.TXT"
OPENIN "PING.TXT"
LINE INPUT #9,a$:PRINT a$:CLOSEIN
```
Deberia mostrar `T:OK servidor listo`
