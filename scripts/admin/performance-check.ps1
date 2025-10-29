# Performance Check Script
# Analyzes system performance and provides recommendations

param(
    [string]$ApiUrl = "http://localhost:3001/admin/v1"
)

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Admin Site Performance Check" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$Results = @{}

# Check API response times
Write-Host "Checking API response times..." -ForegroundColor Yellow

$Endpoints = @(
    "/health",
    "/dashboard",
    "/users?limit=10",
    "/trainers?limit=10",
    "/exercises?limit=10"
)

foreach ($Endpoint in $Endpoints) {
    $Uri = "$ApiUrl$Endpoint"
    
    try {
        $Measure = Measure-Command {
            Invoke-RestMethod -Uri $Uri -Method GET -ErrorAction Stop
        }
        
        $Ms = $Measure.TotalMilliseconds
        $Status = if ($Ms -lt 100) { "✅ Excellent" }
                  elseif ($Ms -lt 300) { "✅ Good" }
                  elseif ($Ms -lt 500) { "⚠️  Acceptable" }
                  else { "❌ Slow" }
        
        Write-Host "  $Endpoint" -NoNewline
        Write-Host " - ${Ms}ms " -NoNewline
        Write-Host $Status
        
        $Results[$Endpoint] = $Ms
    }
    catch {
        Write-Host "  $Endpoint - ❌ Failed" -ForegroundColor Red
    }
}

Write-Host ""

# Check database performance
Write-Host "Checking database performance..." -ForegroundColor Yellow

$DbTests = @(
    "SELECT COUNT(*) FROM users",
    "SELECT COUNT(*) FROM trainers",
    "SELECT COUNT(*) FROM exercises",
    "SELECT * FROM admin_users LIMIT 10"
)

foreach ($Query in $DbTests) {
    try {
        $Measure = Measure-Command {
            psql -h localhost -U postgres -d befreefitness -c "$Query" -q -t
        }
        
        $Ms = $Measure.TotalMilliseconds
        $Status = if ($Ms -lt 50) { "✅" } elseif ($Ms -lt 200) { "⚠️" } else { "❌" }
        
        Write-Host "  $Status Query: ${Ms}ms - $($Query.Substring(0, [Math]::Min(40, $Query.Length)))..."
    }
    catch {
        Write-Host "  ❌ Database query failed" -ForegroundColor Red
    }
}

Write-Host ""

# Check email service
Write-Host "Checking email service (MailHog)..." -ForegroundColor Yellow

try {
    $Response = Invoke-RestMethod -Uri "http://localhost:8025/api/v2/messages" -Method GET
    Write-Host "  ✅ MailHog is running" -ForegroundColor Green
    Write-Host "  Messages in queue: $($Response.total)" -ForegroundColor Cyan
}
catch {
    Write-Host "  ❌ MailHog not accessible" -ForegroundColor Red
}

Write-Host ""

# Check Redis
Write-Host "Checking Redis cache..." -ForegroundColor Yellow

try {
    $RedisInfo = redis-cli INFO 2>$null
    if ($RedisInfo) {
        Write-Host "  ✅ Redis is running" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠️  Redis not running (optional)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠️  Redis not running (optional)" -ForegroundColor Yellow
}

Write-Host ""

# Resource usage
Write-Host "Checking resource usage..." -ForegroundColor Yellow

$NodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($NodeProcesses) {
    $TotalMemoryMB = ($NodeProcesses | Measure-Object WorkingSet -Sum).Sum / 1MB
    $TotalCpuTime = ($NodeProcesses | Measure-Object CPU -Sum).Sum
    
    Write-Host "  Node.js processes: $($NodeProcesses.Count)" -ForegroundColor Cyan
    Write-Host "  Total memory usage: $([Math]::Round($TotalMemoryMB, 2)) MB" -ForegroundColor Cyan
    Write-Host "  Total CPU time: $([Math]::Round($TotalCpuTime, 2))s" -ForegroundColor Cyan
}

$PostgresProcess = Get-Process -Name "postgres" -ErrorAction SilentlyContinue
if ($PostgresProcess) {
    $PgMemoryMB = ($PostgresProcess | Measure-Object WorkingSet -Sum).Sum / 1MB
    Write-Host "  PostgreSQL memory: $([Math]::Round($PgMemoryMB, 2)) MB" -ForegroundColor Cyan
}

Write-Host ""

# Recommendations
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Recommendations" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$AvgResponseTime = ($Results.Values | Measure-Object -Average).Average

if ($AvgResponseTime -gt 500) {
    Write-Host "⚠️  Slow API responses detected" -ForegroundColor Yellow
    Write-Host "   - Consider enabling Redis caching" -ForegroundColor Gray
    Write-Host "   - Optimize database queries" -ForegroundColor Gray
    Write-Host "   - Add database indexes" -ForegroundColor Gray
}
elseif ($AvgResponseTime -gt 300) {
    Write-Host "✅ Performance is acceptable" -ForegroundColor Green
    Write-Host "   - Consider Redis for further optimization" -ForegroundColor Gray
}
else {
    Write-Host "✅ Excellent performance!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Performance check complete" -ForegroundColor Cyan






