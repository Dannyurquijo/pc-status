@echo off
title Detener PC Status
echo ========================================================
echo   Deteniendo Agente PC Status...
echo ========================================================
echo.

powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

echo [OK] Agente de monitoreo detenido limpiamente.
echo.
ping -n 3 127.0.0.1 >nul
