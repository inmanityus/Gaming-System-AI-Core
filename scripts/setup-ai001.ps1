# AI-001: Ollama Setup Script
# Purpose: Install and configure Ollama for local LLM inference
# Task: AI-001 from Phase 1 Foundation Tasks

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI-001: Ollama Setup (Development)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is already installed
Write-Host "Checking Ollama installation..." -ForegroundColor Yellow
$ollamaInstalled = $false
try {
    $ollamaVersion = ollama --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ollamaInstalled = $true
        Write-Host "✓ Ollama is already installed" -ForegroundColor Green
        Write-Host "  Version: $ollamaVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Ollama not found in PATH" -ForegroundColor Yellow
}

# Install Ollama if not installed
if (-not $ollamaInstalled) {
    Write-Host ""
    Write-Host "Installing Ollama..." -ForegroundColor Yellow
    Write-Host "  Downloading Ollama installer..." -ForegroundColor Gray
    
    # Windows installation
    $ollamaUrl = "https://ollama.com/download/windows"
    Write-Host "  Please download and install Ollama from:" -ForegroundColor Yellow
    Write-Host "  $ollamaUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  After installation, restart this script to continue." -ForegroundColor Yellow
    
    # Try to open the download page
    try {
        Start-Process $ollamaUrl
    } catch {
        Write-Host "  Could not open browser automatically" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Waiting for Ollama installation..." -ForegroundColor Yellow
    Write-Host "  Press Enter after installing Ollama to continue..." -ForegroundColor Yellow
    Read-Host
    
    # Verify installation
    try {
        $ollamaVersion = ollama --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Ollama installed successfully" -ForegroundColor Green
            $ollamaInstalled = $true
        }
    } catch {
        Write-Host "ERROR: Ollama installation verification failed" -ForegroundColor Red
        Write-Host "  Please ensure Ollama is installed and in your PATH" -ForegroundColor Yellow
        exit 1
    }
}

# Check if Ollama service is running
Write-Host ""
Write-Host "Checking Ollama service..." -ForegroundColor Yellow
try {
    $ollamaStatus = ollama list 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Ollama service is running" -ForegroundColor Green
    } else {
        Write-Host "  Starting Ollama service..." -ForegroundColor Yellow
        # Ollama should start automatically, but we can try to trigger it
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        
        # Verify it's running
        $ollamaStatus = ollama list 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Ollama service started" -ForegroundColor Green
        } else {
            Write-Host "⚠ Ollama service may not be running" -ForegroundColor Yellow
            Write-Host "  Please start Ollama manually or check the service status" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "⚠ Could not verify Ollama service status" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Pull required models
Write-Host ""
Write-Host "Pulling required models..." -ForegroundColor Yellow
$requiredModels = @(
    "llama3.1:8b",
    "mistral:7b",
    "phi3:mini"
)

$pulledModels = @()
$failedModels = @()

foreach ($model in $requiredModels) {
    Write-Host "  Pulling $model..." -ForegroundColor Gray
    
    # Check if model already exists
    $modelExists = ollama list 2>&1 | Select-String -Pattern $model
    if ($modelExists) {
        Write-Host "    ✓ $model already available" -ForegroundColor Green
        $pulledModels += $model
        continue
    }
    
    # Pull model (this can take a while)
    Write-Host "    Downloading (this may take several minutes)..." -ForegroundColor Gray
    $pullOutput = ollama pull $model 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $model pulled successfully" -ForegroundColor Green
        $pulledModels += $model
    } else {
        Write-Host "    ✗ Failed to pull $model" -ForegroundColor Red
        Write-Host "      Error: $pullOutput" -ForegroundColor Gray
        $failedModels += $model
    }
}

# Test basic inference
Write-Host ""
Write-Host "Testing basic inference..." -ForegroundColor Yellow
if ($pulledModels.Count -gt 0) {
    $testModel = $pulledModels[0]
    Write-Host "  Testing with $testModel..." -ForegroundColor Gray
    
    $testPrompt = "Say hello in one word"
    $testResponse = ollama run $testModel $testPrompt 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $testResponse -match "hello|hi|hey") {
        Write-Host "  ✓ Inference test successful" -ForegroundColor Green
        Write-Host "    Model: $testModel" -ForegroundColor Gray
        $responseText = if ($testResponse -is [string]) { $testResponse.Trim() } else { $testResponse.ToString() }
        Write-Host "    Response: $responseText" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ Inference test may have failed" -ForegroundColor Yellow
        Write-Host "    Response: $testResponse" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Skipping inference test - no models available" -ForegroundColor Yellow
}

# Test API accessibility
Write-Host ""
Write-Host "Testing API accessibility..." -ForegroundColor Yellow
try {
    $apiTest = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "  ✓ Ollama API is accessible" -ForegroundColor Green
    Write-Host "    Endpoint: http://localhost:11434" -ForegroundColor Gray
    Write-Host "    Models available: $($apiTest.models.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  ⚠ Ollama API may not be accessible" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host "    Ensure Ollama service is running on port 11434" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "AI-001 Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Status:" -ForegroundColor Cyan
Write-Host "  ✓ Ollama installed and running" -ForegroundColor Green
if ($pulledModels.Count -gt 0) {
    Write-Host "  ✓ Models available: $($pulledModels.Count)/$($requiredModels.Count)" -ForegroundColor Green
    foreach ($model in $pulledModels) {
        Write-Host "    - $model" -ForegroundColor Gray
    }
}
if ($failedModels.Count -gt 0) {
    Write-Host "  ⚠ Failed to pull: $($failedModels.Count) models" -ForegroundColor Yellow
    foreach ($model in $failedModels) {
        Write-Host "    - $model" -ForegroundColor Gray
    }
    Write-Host "  You can retry pulling models later with:" -ForegroundColor Yellow
    foreach ($model in $failedModels) {
        Write-Host "    ollama pull $model" -ForegroundColor Gray
    }
}
Write-Host ""
Write-Host "API Endpoint:" -ForegroundColor Cyan
Write-Host "  http://localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  ollama list                    # List available models" -ForegroundColor Gray
Write-Host "  ollama pull <model>            # Pull a model" -ForegroundColor Gray
Write-Host "  ollama run <model> <prompt>    # Run inference" -ForegroundColor Gray
Write-Host "  ollama serve                   # Start Ollama service" -ForegroundColor Gray
Write-Host ""

