@echo off
title Desbloquear PC Status
echo ========================================================
echo   Desbloqueando PC Status tras intento de intrusion...
echo ========================================================
echo.

powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/unlock'; Write-Host '[OK] Sistema desbloqueado exitosamente!' -ForegroundColor Green } catch { Write-Host '[ERROR] No se pudo conectar con el agente local en el puerto 5000.' -ForegroundColor Red }"

echo.
ping -n 3 127.0.0.1 >nul
