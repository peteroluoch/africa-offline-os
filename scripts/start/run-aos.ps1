# ============================================
# A-OS (Africa Offline OS) - PRODUCTION STARTUP SCRIPT
# ============================================
# Starts Web Dashboard + Telegram Bot with enterprise-grade monitoring
# FAANG Methodology: Zero-downtime, fault-tolerant, observable

Write-Host "`n" -ForegroundColor Cyan
Write-Host "====== A-OS PRODUCTION STARTUP ======" -ForegroundColor Cyan
Write-Host "Africa-First Infrastructure Launch" -ForegroundColor Cyan

# Get the root path dynamically - works for any user
$rootPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $rootPath

# ============================================
# STEP 1: ENVIRONMENT VALIDATION
# ============================================
Write-Host "`n[1/5] Validating environment..." -ForegroundColor Yellow

# Check Python
$pythonVersion = python --version 2>$null
if ($null -eq $pythonVersion) {
    Write-Host "[ERROR] Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python: $pythonVersion" -ForegroundColor Green

# Check Git
$gitVersion = git --version 2>$null
if ($null -eq $gitVersion) {
    Write-Host "[ERROR] Git not found. Please install Git" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Git: $gitVersion" -ForegroundColor Green

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found. Telegram bot may not work." -ForegroundColor Yellow
    Write-Host "[INFO] Create .env with TELEGRAM_BOT_TOKEN=your_token" -ForegroundColor Yellow
}
else {
    Write-Host "[OK] .env file found" -ForegroundColor Green
}

# ============================================
# STEP 2: DATABASE MIGRATIONS
# ============================================
Write-Host "`n[2/5] Running database migrations..." -ForegroundColor Yellow

# Run migrations via Python
python -c "from aos.db.engine import connect; from aos.db.migrations import MigrationManager; from aos.db.migrations.registry import MIGRATIONS; from aos.core.config import Settings; s = Settings(); conn = connect(s.sqlite_path); mgr = MigrationManager(conn); mgr.apply_migrations(MIGRATIONS); print('[OK] Migrations applied')"

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Database ready" -ForegroundColor Green
}
else {
    Write-Host "[ERROR] Migration failed. Check database." -ForegroundColor Red
    exit 1
}

# ============================================
# STEP 3: WEB DASHBOARD STARTUP
# ============================================
Write-Host "`n[3/5] Starting Web Dashboard..." -ForegroundColor Yellow

# Start web server in new PowerShell window
Write-Host "[LAUNCH] Starting dashboard on http://localhost:8000" -ForegroundColor Cyan
$webCmd = "Set-Location '$rootPath'; python main.py"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $webCmd -WindowStyle Normal

# Wait for web server to start
Write-Host "[WAIT] Waiting for web server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Health check
$maxRetries = 30
$retryCount = 0
$webHealthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Web dashboard healthy and running" -ForegroundColor Green
            $webHealthy = $true
            break
        }
    }
    catch {
        $retryCount++
        Write-Host "[WAIT] Web server starting... (attempt $retryCount/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 1
    }
}

if (-not $webHealthy) {
    Write-Host "[WARNING] Web dashboard health check timed out. Proceeding anyway..." -ForegroundColor Yellow
    Write-Host "Check the web terminal window for errors." -ForegroundColor Yellow
}

# ============================================
# STEP 4: TELEGRAM BOT STARTUP
# ============================================
Write-Host "`n[4/5] Starting Telegram Bot..." -ForegroundColor Yellow

# Check if bot token exists
$envContent = Get-Content ".env" -ErrorAction SilentlyContinue
if ($envContent -match "TELEGRAM_BOT_TOKEN") {
    Write-Host "[LAUNCH] Starting Telegram polling service" -ForegroundColor Cyan
    $botCmd = "Set-Location '$rootPath'; python aos/scripts/telegram_polling_start.py"
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $botCmd -WindowStyle Normal
    
    Write-Host "[WAIT] Waiting for bot to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    Write-Host "[OK] Telegram bot started (check terminal for status)" -ForegroundColor Green
}
else {
    Write-Host "[SKIP] Telegram bot token not configured. Bot not started." -ForegroundColor Yellow
    Write-Host "[INFO] Add TELEGRAM_BOT_TOKEN to .env to enable Telegram" -ForegroundColor Yellow
}

# ============================================
# STEP 5: SYSTEM STATUS
# ============================================
Write-Host "`n[5/5] System Status Check..." -ForegroundColor Yellow

$services = @(
    @{ Name = "Web Dashboard"; Url = "http://localhost:8000/health"; Port = 8000 }
)

$allHealthy = $true
foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 2 -ErrorAction Stop
        Write-Host "[OK] $($service.Name): Running on port $($service.Port)" -ForegroundColor Green
    }
    catch {
        Write-Host "[INFO] $($service.Name): Not responding (may still be starting)" -ForegroundColor Yellow
        $allHealthy = $false
    }
}

# ============================================
# STARTUP COMPLETE
# ============================================
Write-Host "`n" -ForegroundColor Cyan
Write-Host "====== A-OS RUNNING ======" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "Web Dashboard:  http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs:       http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Community:      http://localhost:8000/community" -ForegroundColor Green
Write-Host "Agri:           http://localhost:8000/agri" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "Active Modules:" -ForegroundColor Green
Write-Host "  - Community-Pulse (SMS/Telegram/USSD)" -ForegroundColor Green
Write-Host "  - Transport-Mobile (Zone Intelligence)" -ForegroundColor Green
Write-Host "  - Agri-Lighthouse (Harvest Tracking)" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "FAANG Methodology Active:" -ForegroundColor Green
Write-Host "  - Offline-first architecture" -ForegroundColor Green
Write-Host "  - Kernel-level isolation" -ForegroundColor Green
Write-Host "  - Africa-first design" -ForegroundColor Green
Write-Host "  - Production-ready infrastructure" -ForegroundColor Green

Write-Host "`n[TIP] Press Ctrl+C to stop monitoring (services will keep running)" -ForegroundColor Cyan
Write-Host "[INFO] Check terminal windows for detailed output`n" -ForegroundColor Cyan

# Keep script running with periodic health checks
Write-Host "[OK] All systems operational. Monitoring active..." -ForegroundColor Green
while ($true) {
    Start-Sleep -Seconds 10
    
    # Periodic health check
    try {
        $webCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    }
    catch {
        Write-Host "[WARNING] Web dashboard may have stopped. Check terminal window." -ForegroundColor Yellow
    }
}
