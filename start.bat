@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title DocFusion AI

echo ========================================
echo        DocFusion AI - Launcher
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found in PATH.
  echo Install Python 3.11+ and enable "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Could not create the virtual environment.
    pause
    exit /b 1
  )
)

if not exist ".venv\.deps_installed" (
  echo [2/4] Installing Python dependencies - first run only...
  ".venv\Scripts\python.exe" -m ensurepip --upgrade >nul 2>nul
  ".venv\Scripts\python.exe" -m pip --version >nul 2>nul
  if errorlevel 1 (
    echo ERROR: pip is unavailable inside the virtual environment.
    echo Trying to repair pip with ensurepip...
    ".venv\Scripts\python.exe" -m ensurepip --upgrade
    if errorlevel 1 goto :pip_error
  )
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  if errorlevel 1 goto :pip_error
  ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
  if errorlevel 1 goto :pip_error
  type nul > ".venv\.deps_installed"
) else (
  echo [2/4] Python dependencies already installed.
)

if not exist ".env" (
  echo [3/4] Creating .env from .env.example...
  copy /Y ".env.example" ".env" >nul
  echo.
  echo Add your GEMINI_API_KEY to .env if you want Public AI - Gemini.
  echo Private AI - Ollama does not require a Gemini key.
) else (
  echo [3/4] .env already configured.
)

if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\generated" mkdir "data\generated"
if not exist "data\verification" mkdir "data\verification"
if not exist "data\keys" mkdir "data\keys"

set "OLLAMA_EXE="
where ollama >nul 2>nul
if not errorlevel 1 set "OLLAMA_EXE=ollama"
if not defined OLLAMA_EXE if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"

if defined OLLAMA_EXE (
  curl -s --max-time 2 http://127.0.0.1:11434/api/tags >nul 2>nul
  if errorlevel 1 (
    echo [Ollama] Starting local Ollama service...
    start "DocFusion Ollama" /B "%OLLAMA_EXE%" serve
    timeout /t 2 /nobreak >nul
  ) else (
    echo [Ollama] Already running.
  )
) else (
  echo [Ollama] Not installed. Public Gemini mode will still work.
)

echo [4/4] Starting DocFusion AI...
echo.
echo Waiting for backend to start...

start "DocFusion AI Backend" /B ".venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

set "ATTEMPTS=0"

:wait_for_backend
timeout /t 2 /nobreak >nul
curl -s --max-time 2 http://127.0.0.1:8000 >nul 2>nul

if not errorlevel 1 goto backend_ready

set /a ATTEMPTS+=1
if !ATTEMPTS! GEQ 30 goto backend_error
goto wait_for_backend

:backend_ready
echo.
echo Backend is ready.
echo Opening http://127.0.0.1:8000
start "" "http://127.0.0.1:8000"

echo.
echo DocFusion AI is running.
echo Close this window to stop the launcher.
pause
exit /b 0

:backend_error
echo.
echo ERROR: Backend did not respond within 60 seconds.
echo Check the Python dependencies and backend errors.
pause
exit /b 1
