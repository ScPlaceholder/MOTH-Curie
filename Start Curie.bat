@echo off
rem Double-click this file to start Curie on Windows. Nothing is installed or downloaded.
title Curie, a MOTH project
cd /d "%~dp0"

:menu
echo.
echo   CURIE  -  a quantum-computation microscope
echo.
echo   1. Open the wave bench in your browser   (no Python needed)
echo   2. Run the lessons, step by step         (needs Python)
echo   3. Run a guided tour                     (needs Python)
echo   4. Quit
echo.
set "pick="
set /p "pick=Type a number and press Enter: "
if "%pick%"=="1" goto bench
if "%pick%"=="2" goto lessons
if "%pick%"=="3" goto tour
if "%pick%"=="4" exit /b 0
if not defined pick exit /b 0
echo That was not 1, 2, 3 or 4.
goto menu

:bench
start "" "%~dp0viewer\bench.html"
echo The wave bench is opening in your browser.
goto menu

:findpy
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if defined PY exit /b 0
echo.
echo   Curie needs Python 3.10 or newer, and this computer does not have it.
echo   It is free: https://www.python.org/downloads/
echo   When installing, tick "Add python.exe to PATH". Then double-click this file again.
echo   (Option 1, the wave bench, works without Python.)
exit /b 1

:lessons
call :findpy || goto menu
%PY% -m curie lessons
echo.
pause
goto menu

:tour
call :findpy || goto menu
%PY% -m curie demo q1
echo.
pause
goto menu
