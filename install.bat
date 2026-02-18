@echo off
setlocal EnableDelayedExpansion

REM ─────────────────────────────────────────────────────────────────────────────
REM  Signalis Framework — Installer (Windows)
REM  Double-click to run, or execute from the project folder:  install.bat
REM ─────────────────────────────────────────────────────────────────────────────

echo.
echo  ######  ##  ######  ##   ##  #####  ##     ##  ######
echo  ##      ##  ##      ###  ##  ##  ## ##     ##  ##
echo  ######  ##  ## ###  ## # ##  #####  ##     ##  ######
echo      ##  ##  ##  ##  ##  ###  ##  ## ##     ##      ##
echo  ######  ##  ######  ##   ##  ##  ## ######  ##  ######
echo.
echo  Installer  *  Windows
echo  ________________________________________
echo.

REM ── [1/4] Python ─────────────────────────────────────────────────────────────
echo [1/4] Checking Python...
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo  ERROR: Python not found.
    echo.
    echo  Install Python 3.9+ from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM Check version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo  ERROR: Python 3.9+ required. Found: %PYTHON_VERSION%
    echo  Please upgrade at https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 9 (
    echo  ERROR: Python 3.9+ required. Found: %PYTHON_VERSION%
    echo  Please upgrade at https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo  [OK] Python %PYTHON_VERSION%
echo.

REM ── [2/4] Virtual environment + dependencies ──────────────────────────────────
echo [2/4] Installing dependencies...
echo.

if exist "venv\" (
    echo  [->] Existing venv found, reusing it.
    echo       (Delete the venv folder to start fresh.)
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo  ERROR: Failed to create virtual environment.
        echo  Make sure python3-venv is available and try again.
        echo.
        pause
        exit /b 1
    )
    echo  [OK] Created virtual environment.
)

call venv\Scripts\activate.bat

python -m pip install --upgrade pip --quiet --disable-pip-version-check
python -m pip install -e .[all] --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Dependency installation failed.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo  [OK] Installed (Shaper + Connector -- full install).
echo.

REM ── [3/4] PATH configuration ──────────────────────────────────────────────────
echo [3/4] Adding to PATH...
echo.

set "VENV_SCRIPTS=%~dp0venv\Scripts"

REM Read current user PATH from registry
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"

echo !USER_PATH! | find /i "%VENV_SCRIPTS%" >nul 2>nul
if %errorlevel% neq 0 (
    setx PATH "%VENV_SCRIPTS%;%USER_PATH%" >nul
    echo  [OK] Added to PATH.
    echo  [->] Open a new terminal window for the change to take effect.
) else (
    echo  [OK] Already in PATH.
)
echo.

REM ── [4/4] Configuration ───────────────────────────────────────────────────────
echo [4/4] Configuration...
echo.

if exist ".env" (
    echo  [->] .env already exists, keeping your settings.
) else (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo  [OK] Created .env from template.
    ) else (
        echo  [->] .env.example not found, skipping .env creation.
    )
)
echo.

REM ── Done ──────────────────────────────────────────────────────────────────────
echo  ________________________________________
echo  Installation complete.
echo  ________________________________________
echo.

REM Check if API keys are set
set "HAS_KEYS=0"
findstr /r "EXA_API_KEY=." .env >nul 2>nul && set "HAS_KEYS=1"
findstr /r "OPENAI_API_KEY=." .env >nul 2>nul && set "HAS_KEYS=1"
findstr /r "ANTHROPIC_API_KEY=." .env >nul 2>nul && set "HAS_KEYS=1"

if "%HAS_KEYS%"=="0" (
    echo  API keys not configured.
    echo  Exa + an AI provider are needed for signal and context generation.
    echo.
    set /p run_setup="  Set up API keys now? [Y/n]: "
    echo.
    if /i "!run_setup!" neq "n" (
        venv\Scripts\signalis.exe setup
    ) else (
        echo  Run  signalis setup  whenever you are ready.
    )
) else (
    echo  API keys are configured.
    echo  Run  signalis setup  to update them.
)

echo.
echo  Launch with:
echo.
echo    signalis
echo.
pause
