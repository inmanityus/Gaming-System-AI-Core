# Compile Protocol Buffer Definitions to Python
# Generates Python code from .proto files for binary event serialization

param(
    [string]$ProtoDir = "services\proto",
    [string]$OutputDir = "services\proto"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Compiling Protocol Buffer Definitions ===" -ForegroundColor Cyan
Write-Host ""

# Check if protoc is installed
if (-not (Get-Command protoc -ErrorAction SilentlyContinue)) {
    Write-Host "❌ protoc not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Protocol Buffers compiler:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://github.com/protocolbuffers/protobuf/releases" -ForegroundColor White
    Write-Host "  2. Or install via chocolatey: choco install protoc" -ForegroundColor White
    Write-Host "  3. Or install via winget: winget install Google.Protobuf" -ForegroundColor White
    exit 1
}

Write-Host "✓ protoc found: $(protoc --version)" -ForegroundColor Green
Write-Host ""

# Check Python grpcio-tools (has protoc plugin)
Write-Host "Checking Python grpcio-tools..." -ForegroundColor Yellow
$pythonPath = & "Global-Scripts\verify-tool.ps1" -Tool Python -RequireOrExit
$grpcioCheck = & $pythonPath -m grpc_tools.protoc --version 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing grpcio-tools..." -ForegroundColor Yellow
    & $pythonPath -m pip install grpcio-tools protobuf --quiet
}

Write-Host "✓ grpcio-tools available" -ForegroundColor Green
Write-Host ""

# Find all .proto files
$protoFiles = Get-ChildItem -Path $ProtoDir -Filter "*.proto" -Recurse

if ($protoFiles.Count -eq 0) {
    Write-Host "❌ No .proto files found in $ProtoDir" -ForegroundColor Red
    exit 1
}

Write-Host "Found $($protoFiles.Count) proto file(s):" -ForegroundColor Cyan
$protoFiles | ForEach-Object {
    Write-Host "  - $($_.FullName)" -ForegroundColor White
}
Write-Host ""

# Compile each .proto file
$success = 0
$failed = 0

foreach ($protoFile in $protoFiles) {
    $relativePath = $protoFile.DirectoryName
    $fileName = $protoFile.Name
    
    Write-Host "Compiling $fileName..." -ForegroundColor Yellow
    
    try {
        # Use Python's protoc plugin for better compatibility
        & $pythonPath -m grpc_tools.protoc `
            --proto_path=$ProtoDir `
            --python_out=$OutputDir `
            --grpc_python_out=$OutputDir `
            $protoFile.FullName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Compiled successfully" -ForegroundColor Green
            $success++
        } else {
            Write-Host "  ✗ Compilation failed" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "=== Compilation Summary ===" -ForegroundColor Cyan
Write-Host "✓ Successful: $success" -ForegroundColor Green
Write-Host "✗ Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })
Write-Host ""

if ($success -gt 0) {
    Write-Host "Generated Python modules:" -ForegroundColor Cyan
    Get-ChildItem -Path $OutputDir -Filter "*_pb2.py" | ForEach-Object {
        Write-Host "  - $($_.Name)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "✅ Ready for binary event serialization!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage in code:" -ForegroundColor Cyan
    Write-Host "  from proto import events_pb2" -ForegroundColor Yellow
    Write-Host "  from binary_event_publisher import publish_binary_event" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  await publish_binary_event('weather.changed', data)" -ForegroundColor Yellow
}

if ($failed -gt 0) {
    Write-Host "⚠️  Some files failed to compile. Check errors above." -ForegroundColor Yellow
    exit 1
}

