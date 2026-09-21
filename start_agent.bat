@echo off
title Iniciar PC Status y Tunel Cloudflare
echo ========================================================
echo   Iniciando Agente PC Status y Tunel Cloudflare...
echo ========================================================
echo.

cd /d "%~dp0agent"
start "" pythonw main.py

cd /d "%~dp0"
if exist "cloudflared.exe" (
    start "" /b cmd /c "cloudflared.exe tunnel --url http://localhost:5000 > cloudflare_tunnel.log 2>&1"
    echo [OK] Tunel de Cloudflare iniciado en segundo plano.
) else (
    echo [AVISO] No se encontro cloudflared.exe en el directorio.
)

echo [OK] Agente de monitoreo iniciado en http://localhost:5000
echo Se apagara automaticamente al ejecutar stop_agent.bat o apagar la laptop.
echo.
ping -n 3 127.0.0.1 >nul
