@echo off
title Desinstalador de Inicio Automatico - PC Status
echo ========================================================
echo   Eliminando PC Status del Inicio de Windows
echo ========================================================
echo.

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_FILE=%STARTUP_DIR%\run_pc_status.vbs

if exist "%VBS_FILE%" (
    del "%VBS_FILE%"
    echo [OK] Acceso directo eliminado correctamente de Inicio.
) else (
    echo [INFO] No se encontro PC Status en el Inicio de Windows.
)

echo.
echo ========================================================
echo   DESINSTALACION COMPLETADA
echo ========================================================
echo.
pause
