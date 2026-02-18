#
# Signalis Framework — Installer (Windows PowerShell)
#
# Usage:
#   Right-click > Run with PowerShell
#   Or from terminal:  powershell -ExecutionPolicy Bypass -File install.ps1
#

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ███████╗██╗ ██████╗ ███╗   ██╗  █████╗ ██╗     ██╗███████╗" -ForegroundColor Cyan
Write-Host "  ██╔════╝██║██╔════╝ ████╗  ██║ ██╔══██╗██║     ██║██╔════╝" -ForegroundColor Cyan
Write-Host "  ███████╗██║██║  ███╗██╔██╗ ██║ ███████║██║     ██║███████╗" -ForegroundColor Cyan
Write-Host "  ╚════██║██║██║   ██║██║╚██╗██║ ██╔══██║██║     ██║╚════██║" -ForegroundColor Cyan
Write-Host "  ███████║██║╚██████╔╝██║ ╚████║ ██║  ██║███████╗██║███████║" -ForegroundColor Cyan
Write-Host "  ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Installer  ·  Windows PowerShell" -ForegroundColor DarkGray
Write-Host ""

# ── Helpers ─────────────────────────────────────────────────────────────────
function Write-OK($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [->] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  [!!] $msg" -ForegroundColor Red }
function Write-Dim($msg)  { Write-Host "  $msg" -ForegroundColor DarkGray }

function Exit-WithError($msg) {
    Write-Host ""
    Write-Err $msg
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# ── [1/4] Python ─────────────────────────────────────────────────────────────
Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
Write-Host ""

$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}

if (-not $pythonCmd) {
    Write-Host ""
    Write-Err "Python not found."
    Write-Host ""
    Write-Host "  Install Python 3.9+ from:"
    Write-Host "    https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host '  IMPORTANT: Check "Add Python to PATH" during installation.' -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python version (3.9+ required)
$versionOutput = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>&1
$major = & $pythonCmd -c "import sys; print(sys.version_info.major)" 2>&1
$minor = & $pythonCmd -c "import sys; print(sys.version_info.minor)" 2>&1

if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 9)) {
    Write-Host ""
    Write-Err "Python 3.9+ required. Found: $versionOutput"
    Write-Host ""
    Write-Host "  Upgrade at https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-OK "Python $versionOutput"

# ── [2/4] Virtual environment + dependencies ──────────────────────────────────
Write-Host ""
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path "venv") {
    Write-Warn "Existing venv found — reusing it."
    Write-Dim "(Delete the venv folder to start fresh.)"
} else {
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError "Failed to create virtual environment."
    }
    Write-OK "Created virtual environment."
}

& .\venv\Scripts\Activate.ps1

pip install --upgrade pip --quiet --disable-pip-version-check
pip install -e '.[all]' --quiet --disable-pip-version-check

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Err "Dependency installation failed."
    Write-Host "  Check your internet connection and try again." -ForegroundColor DarkGray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-OK "Installed (Shaper + Connector — full install)."

# ── [3/4] PATH configuration ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Adding to PATH..." -ForegroundColor Cyan
Write-Host ""

$venvScripts = (Resolve-Path ".\venv\Scripts").Path
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

if ($userPath -notlike "*$venvScripts*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$venvScripts;$userPath", "User")
    Write-OK "Added to PATH."
    Write-Warn "Open a new terminal window for the change to take effect."
} else {
    Write-OK "Already in PATH."
}

# ── [4/4] Configuration ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Configuration..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".env") {
    Write-Warn ".env already exists — keeping your settings."
} else {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-OK "Created .env from template."
    } else {
        Write-Warn ".env.example not found — skipping .env creation."
    }
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ________________________________________" -ForegroundColor DarkGray
Write-Host "  Installation complete." -ForegroundColor Green
Write-Host "  ________________________________________" -ForegroundColor DarkGray
Write-Host ""

# Prompt for API key setup if keys are missing (need both Exa AND an AI provider)
$envFile = ".env"
$hasExa = $false
$hasAI  = $false

if (Test-Path $envFile) {
    $hasExa = Select-String -Path $envFile -Pattern "EXA_API_KEY=." -Quiet 2>$null
    $hasAI  = Select-String -Path $envFile -Pattern "(OPENAI_API_KEY|ANTHROPIC_API_KEY)=." -Quiet 2>$null
}

if (-not $hasExa -or -not $hasAI) {
    Write-Host "  API keys not configured." -ForegroundColor Yellow
    Write-Dim "Exa + an AI provider are needed for signals & context."
    Write-Host ""
    $runSetup = Read-Host "  Set up API keys now? [Y/n]"
    Write-Host ""
    if ($runSetup -ne "n" -and $runSetup -ne "N") {
        & .\venv\Scripts\signalis.exe setup
    } else {
        Write-Dim "Run  signalis setup  whenever you are ready."
    }
} else {
    Write-Dim "API keys are configured. Run  signalis setup  to update them."
}

Write-Host ""
Write-Host "  Launch with:"
Write-Host ""
Write-Host "    signalis" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
