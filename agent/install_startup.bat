@echo off
title Instalador de Inicio Automatico - PC Status
echo ========================================================
echo   Instalando PC Status en el Inicio de Windows
echo ========================================================
echo.

set SCRIPT_DIR=%~dp0
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_FILE=%STARTUP_DIR%\run_pc_status.vbs

echo Creando acceso directo silencioso en:
echo %VBS_FILE%
echo.

(
echo Set WshShell = CreateObject("WScript.Shell"^)...
echo WshShell.Run "pythonw """ ^& "%SCRIPT_DIR%main.py" ^& """", 0, False
) > "%VBS_FILE%"

echo ========================================================
echo   INSTALACION COMPLETADA EXITOSAMENTE!
echo   PC Status iniciara automaticamente cada vez que
echo   enciendas tu computadora sin mostrar ventanas.
echo ========================================================
echo.
pause
