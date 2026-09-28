# ABYSSEYE Windows Deployment & Health Verification
$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  ABYSSEYE — Industrial Windows Deployment Automation           " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Check .env
if (-not (Test-Path ".env")) {
    Write-Host "[*] Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 2. Run Test Suite
Write-Host "[*] Running verification test suite..." -ForegroundColor Yellow
python -m pytest -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Tests failed. Aborting deployment." -ForegroundColor Red
    exit 1
}

# 3. Launch Docker Compose
Write-Host "[*] Launching production Docker stack..." -ForegroundColor Yellow
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify Health
Write-Host "[*] Polling service health probes..." -ForegroundColor Yellow
$retries = 15
$healthy = $false

while ($retries -gt 0 -and -not $healthy) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/healthz" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        # continue polling
    }
    Write-Host "    Waiting for services to become healthy ($retries remaining)..."
    Start-Sleep -Seconds 3
    $retries--
}

if (-not $healthy) {
    Write-Host "[ERROR] Deployment healthcheck timed out. Displaying logs:" -ForegroundColor Red
    docker compose -f docker-compose.prod.yml logs
    exit 1
}

Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  [SUCCESS] ABYSSEYE Deployed & Healthy!                        " -ForegroundColor Green
Write-Host "  Web UI: http://localhost                                      " -ForegroundColor Green
Write-Host "  API Health: http://localhost/api/v1/sonar/health              " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
