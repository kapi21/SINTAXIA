# Genera dist/SINTAXIA_Demo_v1.zip para repartir (demo jugable).
# Uso (desde la raiz del repo):
#   powershell -ExecutionPolicy Bypass -File tools\pack_jugador.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $root "run_server.bat"))) {
  $root = Get-Location
}
Set-Location $root

$pkgName = "SINTAXIA_Demo_v1"
$staging = Join-Path $root "dist\$pkgName"
$zipPath = Join-Path $root "dist\$pkgName.zip"

if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
# Quitar paquete antiguo con otro nombre si existe
Get-ChildItem (Join-Path $root "dist") -Filter "SINTAXIA_jugador_*.zip" -ErrorAction SilentlyContinue |
  Remove-Item -Force
Get-ChildItem (Join-Path $root "dist") -Directory -Filter "SINTAXIA_jugador_*" -ErrorAction SilentlyContinue |
  Remove-Item -Recurse -Force

New-Item -ItemType Directory -Force -Path @(
  "$staging\01_PC\server\prompts",
  "$staging\01_PC\server\saves",
  "$staging\01_PC\server\web",
  "$staging\02_microSD",
  "$staging\03_docs"
) | Out-Null

Copy-Item "$root\run_server.bat" "$staging\01_PC\run_server.bat"
@(
  "__init__.py","ai_adventure.py","cpc_text.py","game_state.py","llm_providers.py",
  "protocol.py","save_game.py","server.py","settings_store.py"
) | ForEach-Object { Copy-Item "$root\server\$_" "$staging\01_PC\server\$_" }
Copy-Item "$root\server\prompts\*" "$staging\01_PC\server\prompts\"
Copy-Item "$root\server\saves\.gitkeep" "$staging\01_PC\server\saves\"
Copy-Item "$root\server\web\*" "$staging\01_PC\server\web\"

@(
  "sintaxia.bas","aventura.bas","aventuramode2.bas",
  "TITLE.SCR","T2.SCR","TITLE2.SCR"
) | ForEach-Object { Copy-Item "$root\client\$_" "$staging\02_microSD\$_" }
"192.168.1.4:8080" | Set-Content -Encoding ascii "$staging\02_microSD\HOST.TXT.ejemplo"

Copy-Item "$root\docs\GUIA_JUGADOR.md","$root\docs\MANUAL.md","$root\docs\CARGA.md" "$staging\03_docs\"
Copy-Item "$root\LICENSE" "$staging\LICENSE"

@"
SINTAXIA — Demo Version 1
=========================
Aventura conversacional IA para Amstrad CPC + M4 Board + PC.
Paquete de demostracion jugable (no es una version final de producto).

Licencia: MIT (ver LICENSE)

Contenido
---------
01_PC\       Servidor Python + panel web (run_server.bat)
02_microSD\  Copiar TODO a la microSD (misma carpeta)
03_docs\     Guia del jugador, manual y carga
LICENSE

Como empezar
------------
1) PC: entra en 01_PC y ejecuta run_server.bat
   Panel: http://127.0.0.1:8080/ui  (Mock para probar, o IA + Guardar)
2) microSD: copia el contenido de 02_microSD a la tarjeta
   Renombra HOST.TXT.ejemplo -> HOST.TXT con la IP de tu PC (ej. 192.168.1.10:8080)
3) CPC: |NETSTAT  luego  RUN"sintaxia  -> 1 (MODE 1) o 2 (MODE 2)

Notas
-----
- TITLE.SCR = titulo MODE 1
- T2.SCR = titulo MODE 2 (cabecera AMSDOS; misma carpeta que los .bas)
- Misma Wi-Fi PC y M4; firewall Windows: TCP 8080
- Requiere Python 3.10+ en el PC

Mas detalle: 03_docs\GUIA_JUGADOR.md
"@ | Set-Content -Encoding utf8 "$staging\LEEME.txt"

@"
SINTAXIA Demo v1 - copia TODO a la microSD.
CPC: RUN"sintaxia
HOST.TXT = IP:puerto del PC
"@ | Set-Content -Encoding utf8 "$staging\02_microSD\LEEME_SD.txt"

@"
SINTAXIA Demo v1 - PC
run_server.bat -> http://127.0.0.1:8080/ui
"@ | Set-Content -Encoding utf8 "$staging\01_PC\LEEME_PC.txt"

# VERSION.txt visible al descomprimir
@"
SINTAXIA
Demo Version 1
Fecha paquete: $(Get-Date -Format "yyyy-MM-dd")
"@ | Set-Content -Encoding utf8 "$staging\VERSION.txt"

Compress-Archive -Path $staging -DestinationPath $zipPath -Force
Write-Host "OK $zipPath ($((Get-Item $zipPath).Length) bytes)"
