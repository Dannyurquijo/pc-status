@echo off
title Iniciar PC Status
echo ========================================================
echo   Iniciando Agente PC Status bajo demanda...
echo ========================================================
echo.

cd /d "%~dp0agent"
start "" pythonw main.py

echo [OK] Agente de monitoreo iniciado en segundo plano en http://localhost:5000
echo Se apagara automaticamente cuando apagues tu computadora o cuando ejecutes stop_agent.bat.
echo.
ping -n 3 127.0.0.1 >nul
