# Prepare build context for services that need shared modules
param(
    [Parameter(Mandatory=$true)]
    [string]$ServicePath,
    
    [Parameter(Mandatory=$true)]
    [string]$BuildContextPath
)

Write-Host "Preparing build context for $ServicePath..." -ForegroundColor Cyan

# Create build context directory
if (Test-Path $BuildContextPath) {
    Remove-Item -Path $BuildContextPath -Recurse -Force
}
New-Item -ItemType Directory -Path $BuildContextPath -Force | Out-Null

# Copy service files
Write-Host "Copying service files..." -ForegroundColor Yellow
Copy-Item -Path "$ServicePath/*" -Destination $BuildContextPath -Recurse -Force

# Copy shared modules
if (Test-Path "services/shared") {
    Write-Host "Copying shared modules..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "$BuildContextPath/shared" -Force | Out-Null
    Copy-Item -Path "services/shared/*" -Destination "$BuildContextPath/shared" -Recurse -Force
}

Write-Host "Build context prepared at $BuildContextPath" -ForegroundColor Green
