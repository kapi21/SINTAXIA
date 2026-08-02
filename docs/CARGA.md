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
1. Copia `client/aventura.bas` a la raiz (o carpeta) de la microSD de la M4.
2. Si `RUN"aventura` no carga (fichero ASCII sin cabecera AMSDOS):
   - Abre WinAPE/CPCemu, pega el listado, `SAVE"aventura`
   - Copia el `.bas` generado a la SD
   - O teclea el listado en el CPC y `SAVE"aventura`
3. Alternativa M4 Web UI: `http://192.168.1.128` → subir fichero.

## En el CPC
```
|NETSTAT
RUN"aventura
```
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
