@echo off
title Detener PC Status y Tunel Cloudflare
echo ========================================================
echo   Deteniendo Agente PC Status y Tunel Cloudflare...
echo ========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { ($_.CommandLine -and $_.CommandLine.Contains('main.py')) -or $_.Name -eq 'cloudflared.exe' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

echo [OK] Agente de monitoreo y tunel Cloudflare detenidos limpiamente.
echo.
ping -n 3 127.0.0.1 >nul
