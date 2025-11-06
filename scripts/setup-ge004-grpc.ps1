# GE-004: gRPC Integration Setup Guide
# Purpose: Set up TurboLink plugin and gRPC service integration
# Task: GE-004 from Phase 3 Advanced Features

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GE-004: gRPC Integration Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "TurboLink Plugin Installation:" -ForegroundColor Yellow
Write-Host "  1. Open Epic Games Launcher" -ForegroundColor White
Write-Host "  2. Go to Unreal Engine → Marketplace" -ForegroundColor White
Write-Host "  3. Search for 'TurboLink'" -ForegroundColor White
Write-Host "  4. Install TurboLink plugin" -ForegroundColor White
Write-Host "  5. Enable plugin in UE5 project" -ForegroundColor White
Write-Host ""

Write-Host "Alternative: Manual Installation" -ForegroundColor Yellow
Write-Host "  1. Download TurboLink from GitHub: https://github.com/Phyronnaz/TurboLink" -ForegroundColor White
Write-Host "  2. Copy to unreal/Plugins/TurboLink/" -ForegroundColor White
Write-Host "  3. Regenerate project files" -ForegroundColor White
Write-Host ""

Write-Host "gRPC Service Setup:" -ForegroundColor Yellow
Write-Host "  1. Install Protocol Buffers compiler (protoc)" -ForegroundColor White
Write-Host "  2. Generate C++ code from .proto files:" -ForegroundColor White
Write-Host "     protoc --cpp_out=unreal/Source/BodyBroker/ unreal/Source/BodyBroker/bodybroker.proto" -ForegroundColor Gray
Write-Host "  3. Use TurboLink code generator for UE5 integration" -ForegroundColor White
Write-Host ""

Write-Host "Backend gRPC Server:" -ForegroundColor Yellow
Write-Host "  • gRPC server implementation: services/ai_integration/grpc_server.py" -ForegroundColor White
Write-Host "  • Port: 50051 (default gRPC port)" -ForegroundColor White
Write-Host "  • Service: AIInferenceService" -ForegroundColor White
Write-Host ""

Write-Host "Files Created:" -ForegroundColor Cyan
Write-Host "  ✓ unreal/Source/BodyBroker/BodyBrokerGRPCClient.h" -ForegroundColor Green
Write-Host "  ✓ unreal/Source/BodyBroker/BodyBrokerGRPCClient.cpp" -ForegroundColor Green
Write-Host "  ✓ unreal/Source/BodyBroker/bodybroker.proto" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Install TurboLink plugin" -ForegroundColor White
Write-Host "  2. Generate gRPC code from .proto file" -ForegroundColor White
Write-Host "  3. Uncomment TurboLink code in BodyBrokerGRPCClient.cpp" -ForegroundColor White
Write-Host "  4. Implement backend gRPC server (services/ai_integration/grpc_server.py)" -ForegroundColor White
Write-Host "  5. Test gRPC connection" -ForegroundColor White
Write-Host ""

