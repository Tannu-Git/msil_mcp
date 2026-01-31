# MSIL MCP Server - Quick Start Demo Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   MSIL MCP Server - Demo Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# Check if ports are already in use
Write-Host "Checking ports..." -ForegroundColor Yellow
$portsToCheck = @{
    8000 = "MCP Server"
    5174 = "Admin UI"
    5173 = "Chat UI"
}

$portsInUse = @()
foreach ($port in $portsToCheck.Keys) {
    if (Test-Port -Port $port) {
        $portsInUse += "$($portsToCheck[$port]) (port $port)"
    }
}

if ($portsInUse.Count -gt 0) {
    Write-Host "Warning: The following services are already running:" -ForegroundColor Yellow
    foreach ($service in $portsInUse) {
        Write-Host "  - $service" -ForegroundColor Yellow
    }
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Startup cancelled." -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "Starting services in separate windows..." -ForegroundColor Green
Write-Host ""

# Start MCP Server
Write-Host "[1/3] Starting MCP Server (http://localhost:8000)..." -ForegroundColor Cyan
$mcpServerPath = Join-Path $scriptDir "mcp-server"
$mcpCmd = "cd '$mcpServerPath'; python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $mcpCmd

Start-Sleep -Seconds 2

# Start Admin UI
Write-Host "[2/3] Starting Admin UI (http://localhost:5174)..." -ForegroundColor Cyan
$adminUiPath = Join-Path $scriptDir "admin-ui"
$adminCmd = "cd '$adminUiPath'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $adminCmd

Start-Sleep -Seconds 2

# Start Chat UI
Write-Host "[3/3] Starting Chat UI (http://localhost:5173)..." -ForegroundColor Cyan
$chatUiPath = Join-Path $scriptDir "chat-ui"
$chatCmd = "cd '$chatUiPath'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $chatCmd

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   All services starting up!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor White
Write-Host "  MCP Server:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  Admin UI:    http://localhost:5174" -ForegroundColor Yellow
Write-Host "  Chat UI:     http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Demo Resources:" -ForegroundColor White
Write-Host "  Demo Guide:  E2E_DEMO_GUIDE.md" -ForegroundColor Yellow
Write-Host "  Sample API:  sample-apis/customer-service-api.yaml" -ForegroundColor Yellow
Write-Host ""
Write-Host "Wait 10-15 seconds for all services to be ready..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop services" -ForegroundColor Gray
Write-Host ""

# Wait for services to start
Write-Host "Waiting for services to initialize..." -ForegroundColor Cyan
$maxAttempts = 30
$attempt = 0
$allRunning = $false

while ($attempt -lt $maxAttempts -and -not $allRunning) {
    $attempt++
    Start-Sleep -Seconds 1
    
    $mcpRunning = Test-Port -Port 8000
    $adminRunning = Test-Port -Port 5174
    $chatRunning = Test-Port -Port 5173
    
    $runningCount = ($mcpRunning, $adminRunning, $chatRunning | Where-Object { $_ }).Count
    
    Write-Host "  Checking services... ($runningCount/3 ready)" -ForegroundColor Gray
    
    if ($mcpRunning -and $adminRunning -and $chatRunning) {
        $allRunning = $true
    }
}

if ($allRunning) {
    Write-Host ""
    Write-Host "✅ All services are ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  1. Open Admin UI: http://localhost:5174" -ForegroundColor Yellow
    Write-Host "  2. Click 'Import OpenAPI' in sidebar" -ForegroundColor Yellow
    Write-Host "  3. Upload sample-apis/customer-service-api.yaml" -ForegroundColor Yellow
    Write-Host "  4. Follow E2E_DEMO_GUIDE.md for complete demo flow" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "⚠️  Some services may still be starting up..." -ForegroundColor Yellow
    Write-Host "Please check the individual terminal windows for errors" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit this window (services will keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
