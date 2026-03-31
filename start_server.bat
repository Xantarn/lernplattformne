@echo off
setlocal

REM Projektpfad
set "PROJECT_DIR=C:\Users\xanta\Documents\PPlatform\lernplattform"

REM Python aus deiner aktiven Virtu-venv
set "PYTHON_EXE=C:\Users\xanta\Documents\Virtu\Django\Scripts\python.exe"

cd /d "%PROJECT_DIR%"

if not exist "%PYTHON_EXE%" (
    echo Fehler: Python wurde nicht gefunden:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

echo Starte Django-Server mit:
echo %PYTHON_EXE% manage.py runserver
echo.

"%PYTHON_EXE%" manage.py runserver

if errorlevel 1 (
    echo.
    echo Server wurde mit Fehler beendet.
    pause
)

endlocal
