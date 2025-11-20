# Fix workflow branch names from 'main' to 'master'
Write-Host "Updating GitHub Actions workflows to use 'master' branch..." -ForegroundColor Cyan

$workflowPath = ".github/workflows"
$updated = 0

Get-ChildItem -Path $workflowPath -Filter "*.yml" | ForEach-Object {
    $file = $_.FullName
    $content = Get-Content $file -Raw
    $originalContent = $content
    
    # Replace branch references
    $content = $content -replace 'branches:\s*\[main\]', 'branches: [master]'
    $content = $content -replace 'branches:\s*\[main,', 'branches: [master,'
    $content = $content -replace ',\s*main\]', ', master]'
    $content = $content -replace ',\s*main,', ', master,'
    $content = $content -replace 'branch:\s*main', 'branch: master'
    $content = $content -replace '"main"', '"master"'
    $content = $content -replace "'main'", "'master'"
    
    if ($content -ne $originalContent) {
        Set-Content -Path $file -Value $content -NoNewline
        Write-Host "  ✅ Updated: $($_.Name)" -ForegroundColor Green
        $updated++
    }
}

Write-Host "`nUpdated $updated workflow files" -ForegroundColor Yellow

# Also update services.json if it contains branch references
$servicesJson = ".github/services.json"
if (Test-Path $servicesJson) {
    $content = Get-Content $servicesJson -Raw
    $originalContent = $content
    
    $content = $content -replace '"main"', '"master"'
    
    if ($content -ne $originalContent) {
        Set-Content -Path $servicesJson -Value $content -NoNewline
        Write-Host "  ✅ Updated: services.json" -ForegroundColor Green
    }
}

Write-Host "`nDone! Workflows will now trigger on 'master' branch" -ForegroundColor Green
