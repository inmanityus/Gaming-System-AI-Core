# Invoke SageMaker Async Inference for Bronze Tier
# Purpose: Submit inference requests to SageMaker async endpoint
# Use Cases: Storyteller, Cybersecurity, Admin operations

param(
    [Parameter(Mandatory=$true)]
    [string]$EndpointName,
    
    [Parameter(Mandatory=$true)]
    [string]$InputContent,
    
    [string]$Region = "us-east-1",
    
    [string]$OutputS3Bucket = "gaming-ai-async-output-dev",
    
    [string]$OutputS3Key = "inferences/$(Get-Date -Format 'yyyyMMdd-HHmmss')/request.json",
    
    [int]$TimeoutSeconds = 300
)

Write-Host "[BRONZE TIER] Invoking async inference..." -ForegroundColor Cyan
Write-Host "  Endpoint: $EndpointName" -ForegroundColor White
Write-Host "  Region: $Region" -ForegroundColor White
Write-Host "  Output: s3://$OutputS3Bucket/$OutputS3Key" -ForegroundColor White

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] AWS CLI not found. Install: winget install Amazon.AWSCLI" -ForegroundColor Red
    exit 1
}

# Upload input to S3
$tempInputFile = [System.IO.Path]::GetTempFileName()
$InputContent | Out-File -FilePath $tempInputFile -Encoding utf8

Write-Host "[STEP 1] Uploading input to S3..." -ForegroundColor Yellow
aws s3 cp $tempInputFile "s3://$OutputS3Bucket/inputs/$OutputS3Key" --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to upload input to S3" -ForegroundColor Red
    Remove-Item $tempInputFile -Force
    exit 1
}

$inputLocation = "s3://$OutputS3Bucket/inputs/$OutputS3Key"

# Invoke async endpoint
Write-Host "[STEP 2] Invoking SageMaker async endpoint..." -ForegroundColor Yellow

$invokeOutput = aws sagemaker-runtime invoke-async-endpoint `
    --endpoint-name $EndpointName `
    --input-location $inputLocation `
    --output-location "s3://$OutputS3Bucket/outputs/$OutputS3Key" `
    --region $Region `
    --output json 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to invoke async endpoint" -ForegroundColor Red
    Write-Host $invokeOutput -ForegroundColor Red
    Remove-Item $tempInputFile -Force
    exit 1
}

$response = $invokeOutput | ConvertFrom-Json
$outputLocation = $response.OutputLocation

Write-Host "[SUCCESS] Async inference invoked" -ForegroundColor Green
Write-Host "  Output Location: $outputLocation" -ForegroundColor White
Write-Host "[WAIT] Waiting for result (timeout: $TimeoutSeconds seconds)..." -ForegroundColor Yellow

# Poll for result
$elapsed = 0
$pollInterval = 5

while ($elapsed -lt $TimeoutSeconds) {
    Start-Sleep -Seconds $pollInterval
    $elapsed += $pollInterval
    
    # Check if output file exists
    $outputS3Uri = [System.Uri]::new($outputLocation)
    $bucket = $outputS3Uri.Host.Split('.')[0]
    $key = $outputS3Uri.AbsolutePath.TrimStart('/')
    
    $outputExists = aws s3 ls "s3://$bucket/$key" --region $Region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Result available!" -ForegroundColor Green
        Write-Host "[DOWNLOAD] Downloading result..." -ForegroundColor Yellow
        
        $outputFile = [System.IO.Path]::GetTempFileName()
        aws s3 cp "s3://$bucket/$key" $outputFile --region $Region
        
        if ($LASTEXITCODE -eq 0) {
            $result = Get-Content $outputFile -Raw
            Write-Host "[RESULT]" -ForegroundColor Cyan
            Write-Host $result -ForegroundColor White
            
            Remove-Item $outputFile -Force
        }
        
        Remove-Item $tempInputFile -Force
        exit 0
    }
    
    Write-Host "  Waiting... ($elapsed/$TimeoutSeconds seconds)" -ForegroundColor Gray
}

Write-Host "[TIMEOUT] Result not available within timeout period" -ForegroundColor Yellow
Write-Host "  Check output location manually: $outputLocation" -ForegroundColor White
Remove-Item $tempInputFile -Force






