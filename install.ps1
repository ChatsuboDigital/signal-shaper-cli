#
# Signalis Framework — Installer (Windows PowerShell)
#
# Usage:
#   Right-click > Run with PowerShell
#   Or from terminal:  powershell -ExecutionPolicy Bypass -File install.ps1
#

Write-Host ""
Write-Host "  ███████╗██╗ ██████╗ ███╗   ██╗  █████╗ ██╗     ██╗███████╗" -ForegroundColor Cyan
Write-Host "  ██╔════╝██║██╔════╝ ████╗  ██║ ██╔══██╗██║     ██║██╔════╝" -ForegroundColor Cyan
Write-Host "  ███████╗██║██║  ███╗██╔██╗ ██║ ███████║██║     ██║███████╗" -ForegroundColor Cyan
Write-Host "  ╚════██║██║██║   ██║██║╚██╗██║ ██╔══██║██║     ██║╚════██║" -ForegroundColor Cyan
Write-Host "  ███████║██║╚██████╔╝██║ ╚████║ ██║  ██║███████╗██║███████║" -ForegroundColor Cyan
Write-Host "  ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Installer · Windows PowerShell" -ForegroundColor DarkGray
Write-Host ""

# ── [1/4] Python ─────────────────────────────────────────────────────────────
Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan

$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}

if (-not $pythonCmd) {
    Write-Host ""
    Write-Host "  ERROR: Python not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Install Python 3.9+ from https://www.python.org/downloads/"
    Write-Host '  Make sure to check "Add Python to PATH" during installation.'
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonVersion = & $pythonCmd --version 2>&1
Write-Host "  OK  $pythonVersion" -ForegroundColor Green

# ── [2/4] Virtual environment ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Cyan

if (Test-Path "venv") {
    Write-Host "  venv\ already exists — reusing it." -ForegroundColor Yellow
    Write-Host "  (Delete the venv folder to reinstall from scratch.)" -ForegroundColor DarkGray
} else {
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to create virtual environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "  Created venv\" -ForegroundColor Green
}

& .\venv\Scripts\Activate.ps1
Write-Host "  Activated" -ForegroundColor Green

# ── [3/4] Install dependencies ────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Cyan

pip install --upgrade pip --quiet --disable-pip-version-check
pip install -e .[all] --quiet --disable-pip-version-check

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Dependency installation failed." -ForegroundColor Red
    Write-Host "  Check your internet connection and try again."
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "  OK  Installed (Shaper + Connector — full install)" -ForegroundColor Green

# ── [4/4] Configuration ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Configuration..." -ForegroundColor Cyan

if (Test-Path ".env") {
    Write-Host "  .env already exists — keeping your settings." -ForegroundColor Yellow
} else {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "  Created .env from template." -ForegroundColor Green
    } else {
        Write-Host "  .env.example not found — skipping .env creation." -ForegroundColor Yellow
    }
}

# Add venv\Scripts to user PATH
$venvScripts = (Resolve-Path ".\venv\Scripts").Path
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$venvScripts*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$venvScripts;$userPath", "User")
    Write-Host "  Added venv\Scripts to PATH." -ForegroundColor Green
    Write-Host "  Open a new terminal window for the change to take effect." -ForegroundColor Yellow
} else {
    Write-Host "  PATH already up to date." -ForegroundColor Green
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Installation complete." -ForegroundColor Green
Write-Host ""

# Prompt for API key setup if keys are missing
$envFile = ".env"
$hasExa = Select-String -Path $envFile -Pattern "EXA_API_KEY=." -Quiet 2>$null
$hasAI  = Select-String -Path $envFile -Pattern "(OPENAI_API_KEY|ANTHROPIC_API_KEY)=." -Quiet 2>$null

if (-not $hasExa -or -not $hasAI) {
    Write-Host "  API keys not configured." -ForegroundColor Yellow
    Write-Host "  Exa + an AI provider are needed for signals & context." -ForegroundColor DarkGray
    Write-Host ""
    $runSetup = Read-Host "  Set up API keys now? [Y/n]"
    Write-Host ""
    if ($runSetup -ne "n" -and $runSetup -ne "N") {
        & .\venv\Scripts\signalis.exe setup
    } else {
        Write-Host "  Run  signalis setup  whenever you are ready." -ForegroundColor DarkGray
    }
} else {
    Write-Host "  API keys are configured. Run  signalis setup  to update them." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Launch with:"
Write-Host ""
Write-Host "    signalis" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
