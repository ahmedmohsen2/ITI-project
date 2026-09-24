@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
set "PORT=%~1"
if not defined PORT set "PORT=8000"

if not exist "%PYTHON_EXE%" (
    echo Creating the project virtual environment...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto :error
)

"%PYTHON_EXE%" -c "import django" >nul 2>nul
if errorlevel 1 (
    echo Installing project dependencies...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

if not exist ".env" (
    set "DB_ENGINE=sqlite"
    echo No .env file found. Starting with the local SQLite demo database.
) else (
    echo Loading database settings from .env.
)

echo Applying database migrations...
"%PYTHON_EXE%" manage.py migrate --noinput
if errorlevel 1 goto :database_error

echo Preparing demo products...
"%PYTHON_EXE%" manage.py seed_demo
if errorlevel 1 goto :error

echo Starting Northstar Market at http://127.0.0.1:%PORT%/
"%PYTHON_EXE%" manage.py runserver 127.0.0.1:%PORT%
goto :eof

:database_error
echo Database setup failed. Check the DB settings in .env and confirm PostgreSQL is running.
pause
exit /b 1

:error
echo Startup failed. Review the error above.
pause
exit /b 1
