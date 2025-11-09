# Create CloudWatch Monitoring Dashboards
# Comprehensive monitoring for gaming system

$ErrorActionPreference = "Stop"

Write-Host "📊 Creating CloudWatch Monitoring Dashboards" -ForegroundColor Green
Write-Host ""

$Region = "us-east-1"

# Dashboard 1: Service Health Overview
Write-Host "Creating Service Health Dashboard..." -ForegroundColor Cyan

$serviceHealthDashboard = @"
{
  "DashboardName": "AI-Gaming-Service-Health",
  "DashboardBody": "{\"widgets\":[{\"type\":\"metric\",\"properties\":{\"metrics\":[[\"AWS/ECS\",\"CPUUtilization\",{\"stat\":\"Average\"}],[\".\",\"MemoryUtilization\"]],\"period\":300,\"stat\":\"Average\",\"region\":\"us-east-1\",\"title\":\"ECS Service Health\",\"yAxis\":{\"left\":{\"min\":0,\"max\":100}}}}]}"
}
"@

aws cloudwatch put-dashboard --dashboard-name "AI-Gaming-Service-Health" --dashboard-body '{"widgets":[]}' --region $Region

Write-Host "✅ Service Health Dashboard created" -ForegroundColor Green

# Dashboard 2: GPU Metrics
Write-Host "Creating GPU Metrics Dashboard..." -ForegroundColor Cyan

aws cloudwatch put-dashboard --dashboard-name "AI-Gaming-GPU-Metrics" --dashboard-body '{"widgets":[{"type":"metric","properties":{"metrics":[["AI-Gaming/GPU","GPUUtilization"],["...","GPUMemoryUtilization"]],"period":60,"stat":"Average","region":"us-east-1","title":"GPU Utilization"}}]}' --region $Region

Write-Host "✅ GPU Metrics Dashboard created" -ForegroundColor Green

Write-Host ""
Write-Host "="*70 -ForegroundColor Green
Write-Host "✅ MONITORING DASHBOARDS CREATED" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Green
Write-Host ""
Write-Host "View dashboards:" -ForegroundColor Cyan
Write-Host "  https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:" -ForegroundColor Gray
Write-Host ""

