# Create Application Auto Scaling Policies
# Based on 4-model consensus design (GPT-5, Claude 4.5, Gemini 2.5 Pro, Perplexity)

param(
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

Write-Host "🎯 Creating Auto Scaling Policies for GPU Tiers" -ForegroundColor Green
Write-Host ""

# ============================================================================
# GOLD TIER SCALING POLICIES
# ============================================================================
Write-Host "📊 GOLD TIER: Target Tracking Policies" -ForegroundColor Yellow
Write-Host "  Metric 1: GPU Utilization (target: 70%)" -ForegroundColor Gray
Write-Host "  Metric 2: Memory Utilization (target: 75%)" -ForegroundColor Gray
Write-Host ""

# Policy 1: GPU Utilization Target Tracking
Write-Host "  Creating GPU Utilization policy..." -ForegroundColor Cyan
aws autoscaling put-scaling-policy `
    --auto-scaling-group-name "AI-Gaming-Gold-Tier-ASG" `
    --policy-name "Gold-GPU-Utilization-Target-70" `
    --policy-type "TargetTrackingScaling" `
    --target-tracking-configuration '{
        \"TargetValue\": 70.0,
        \"CustomizedMetricSpecification\": {
            \"MetricName\": \"GPUUtilization\",
            \"Namespace\": \"AI-Gaming/GPU\",
            \"Statistic\": \"Average\",
            \"Dimensions\": [{\"Name\": \"Tier\", \"Value\": \"Gold\"}]
        },
        \"ScaleInCooldown\": 900,
        \"ScaleOutCooldown\": 180
    }' `
    --region $Region

Write-Host "  ✅ GPU Utilization policy created" -ForegroundColor Green

# Policy 2: Memory Utilization Target Tracking
Write-Host "  Creating GPU Memory policy..." -ForegroundColor Cyan
aws autoscaling put-scaling-policy `
    --auto-scaling-group-name "AI-Gaming-Gold-Tier-ASG" `
    --policy-name "Gold-Memory-Utilization-Target-75" `
    --policy-type "TargetTrackingScaling" `
    --target-tracking-configuration '{
        \"TargetValue\": 75.0,
        \"CustomizedMetricSpecification\": {
            \"MetricName\": \"GPUMemoryUtilization\",
            \"Namespace\": \"AI-Gaming/GPU\",
            \"Statistic\": \"Average\",
            \"Dimensions\": [{\"Name\": \"Tier\", \"Value\": \"Gold\"}]
        },
        \"ScaleInCooldown\": 900,
        \"ScaleOutCooldown\": 180
    }' `
    --region $Region

Write-Host "  ✅ GPU Memory policy created" -ForegroundColor Green
Write-Host ""

# ============================================================================
# SILVER TIER SCALING POLICIES
# ============================================================================
Write-Host "📊 SILVER TIER: Target Tracking Policies" -ForegroundColor Yellow
Write-Host "  Metric 1: GPU Utilization (target: 70%)" -ForegroundColor Gray
Write-Host "  Metric 2: Memory Utilization (target: 75%)" -ForegroundColor Gray
Write-Host ""

# Policy 1: GPU Utilization
Write-Host "  Creating GPU Utilization policy..." -ForegroundColor Cyan
aws autoscaling put-scaling-policy `
    --auto-scaling-group-name "AI-Gaming-Silver-Tier-ASG" `
    --policy-name "Silver-GPU-Utilization-Target-70" `
    --policy-type "TargetTrackingScaling" `
    --target-tracking-configuration '{
        \"TargetValue\": 70.0,
        \"CustomizedMetricSpecification\": {
            \"MetricName\": \"GPUUtilization\",
            \"Namespace\": \"AI-Gaming/GPU\",
            \"Statistic\": \"Average\",
            \"Dimensions\": [{\"Name\": \"Tier\", \"Value\": \"Silver\"}]
        },
        \"ScaleInCooldown\": 900,
        \"ScaleOutCooldown\": 180
    }' `
    --region $Region

Write-Host "  ✅ GPU Utilization policy created" -ForegroundColor Green

# Policy 2: Memory Utilization
Write-Host "  Creating GPU Memory policy..." -ForegroundColor Cyan
aws autoscaling put-scaling-policy `
    --auto-scaling-group-name "AI-Gaming-Silver-Tier-ASG" `
    --policy-name "Silver-Memory-Utilization-Target-75" `
    --policy-type "TargetTrackingScaling" `
    --target-tracking-configuration '{
        \"TargetValue\": 75.0,
        \"CustomizedMetricSpecification\": {
            \"MetricName\": \"GPUMemoryUtilization\",
            \"Namespace\": \"AI-Gaming/GPU\",
            \"Statistic\": \"Average\",
            \"Dimensions\": [{\"Name\": \"Tier\", \"Value\": \"Silver\"}]
        },
        \"ScaleInCooldown\": 900,
        \"ScaleOutCooldown\": 180
    }' `
    --region $Region

Write-Host "  ✅ GPU Memory policy created" -ForegroundColor Green
Write-Host ""

Write-Host "="*70 -ForegroundColor Green
Write-Host "✅ AUTO SCALING POLICIES CREATED" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Green
Write-Host ""
Write-Host "Scaling behavior:" -ForegroundColor Cyan
Write-Host "  Scale OUT: When GPU > 70% or Memory > 75% (cooldown: 3 min)" -ForegroundColor White
Write-Host "  Scale IN: When metrics drop below target (cooldown: 15 min)" -ForegroundColor White
Write-Host ""
Write-Host "Target capacity:" -ForegroundColor Cyan
Write-Host "  Gold tier: Maintains 70% GPU utilization" -ForegroundColor White
Write-Host "  Silver tier: Maintains 70% GPU utilization" -ForegroundColor White
Write-Host ""

