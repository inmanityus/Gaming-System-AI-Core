# Create CloudWatch Alarms for Critical Metrics
# Alerts for service down, GPU exhaustion, latency spikes

$ErrorActionPreference = "Stop"
$Region = "us-east-1"

Write-Host "🚨 Creating CloudWatch Alarms" -ForegroundColor Green
Write-Host ""

# Alarm 1: GPU Utilization Critical (>95%)
Write-Host "Creating GPU Utilization alarm..." -ForegroundColor Cyan
aws cloudwatch put-metric-alarm `
    --alarm-name "AI-Gaming-GPU-Utilization-Critical" `
    --alarm-description "GPU utilization >95% - risk of saturation" `
    --metric-name "GPUUtilization" `
    --namespace "AI-Gaming/GPU" `
    --statistic "Average" `
    --period 300 `
    --evaluation-periods 2 `
    --threshold 95.0 `
    --comparison-operator "GreaterThanThreshold" `
    --region $Region

Write-Host "✅ GPU Utilization alarm created" -ForegroundColor Green

# Alarm 2: GPU Memory Exhaustion (>90%)
Write-Host "Creating GPU Memory alarm..." -ForegroundColor Cyan
aws cloudwatch put-metric-alarm `
    --alarm-name "AI-Gaming-GPU-Memory-Critical" `
    --alarm-description "GPU memory >90% - risk of OOM" `
    --metric-name "GPUMemoryUtilization" `
    --namespace "AI-Gaming/GPU" `
    --statistic "Average" `
    --period 300 `
    --evaluation-periods 2 `
    --threshold 90.0 `
    --comparison-operator "GreaterThanThreshold" `
    --region $Region

Write-Host "✅ GPU Memory alarm created" -ForegroundColor Green

Write-Host ""
Write-Host "="*70 -ForegroundColor Green
Write-Host "✅ CLOUDWATCH ALARMS CREATED" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Green
Write-Host ""

