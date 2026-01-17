#!/usr/bin/env pwsh
# Mnemonic - Quick Start Script

Write-Host "🚀 Starting Mnemonic..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check if pnpm is available
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  pnpm not found. Install with: npm install -g pnpm" -ForegroundColor Yellow
    Write-Host "   Falling back to npm..." -ForegroundColor Yellow
    $packageManager = "npm"
} else {
    $packageManager = "pnpm"
}

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env from .env.example" -ForegroundColor Green
        Write-Host "⚠️  Edit .env with your API keys before continuing!" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter after configuring .env"
    } else {
        Write-Host "❌ .env.example not found!" -ForegroundColor Red
        exit 1
    }
}

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing Next.js dependencies..." -ForegroundColor Cyan
    & $packageManager install
}

# Start backend
Write-Host ""
Write-Host "🔧 Starting FastAPI backend on port 8000..." -ForegroundColor Cyan
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python api_server.py" -PassThru

Start-Sleep -Seconds 3

# Start frontend
Write-Host "🎨 Starting Next.js frontend on port 3000..." -ForegroundColor Cyan
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "$packageManager dev" -PassThru

Write-Host ""
Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host "   Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend UI:  http://localhost:3000" -ForegroundColor White
Write-Host "   API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to stop all services..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "🛑 Stopping services..." -ForegroundColor Red
Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue

Write-Host "✅ All services stopped." -ForegroundColor Green
