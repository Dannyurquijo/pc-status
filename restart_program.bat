@echo off
title Reiniciador de Programas - PC Status
echo ========================================================
echo       Reiniciador de Programas para Laptop
echo ========================================================
echo.

python "%~dp0restart_program.py" %*

echo.
pause
