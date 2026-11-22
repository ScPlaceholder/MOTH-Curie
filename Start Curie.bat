@echo off
rem Double-click this file to start Curie on Windows.
rem Options 1-3 install and download nothing. Option 4 asks before it downloads anything.
title Curie, a MOTH project
cd /d "%~dp0"

:menu
echo.
echo   CURIE  -  a quantum-computation microscope
echo.
echo   1. Open the wave bench in your browser   (no Python needed)
echo   2. Run the lessons, step by step         (needs Python)
echo   3. Run a guided tour                     (needs Python)
echo   4. Check Curie against Qiskit and Cirq   (downloads them; asks first)
echo   5. Quit
echo.
set "pick="
set /p "pick=Type a number and press Enter: "
if "%pick%"=="1" goto bench
if "%pick%"=="2" goto lessons
if "%pick%"=="3" goto tour
if "%pick%"=="4" goto xcheck
if "%pick%"=="5" exit /b 0
if not defined pick exit /b 0
echo That was not 1, 2, 3, 4 or 5.
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

:xcheck
call :findpy || goto menu
echo.
echo   This checks Curie against two independent simulators, Qiskit and Cirq.
echo   It downloads them (a few hundred MB) into a private folder here, .venv-xcheck,
echo   so nothing else on this computer changes. Then it runs every test, including
echo   300 random circuits compared against each simulator.
set "ok="
set /p "ok=Go ahead? Type y and press Enter: "
if /i not "%ok%"=="y" goto menu
if not exist ".venv-xcheck\Scripts\python.exe" %PY% -m venv .venv-xcheck
".venv-xcheck\Scripts\python.exe" -m pip install --quiet -e ".[xcheck]" pytest
if errorlevel 1 (
  echo   The download or install did not finish. Check the internet connection and try again.
  pause
  goto menu
)
".venv-xcheck\Scripts\python.exe" -m pytest tests -q
echo.
echo   To remove the cross-checks later, delete the .venv-xcheck folder.
pause
goto menu
