Write-Host "Updating all upload-artifact actions to v4..." -ForegroundColor Cyan

$workflowFiles = Get-ChildItem -Path ".github/workflows" -Filter "*.yml" -Recurse

foreach ($file in $workflowFiles) {
    $content = Get-Content $file.FullName -Raw
    $updated = $content -replace 'upload-artifact@v3', 'upload-artifact@v4'
    
    if ($content -ne $updated) {
        Set-Content -Path $file.FullName -Value $updated
        Write-Host "  ✅ Updated: $($file.Name)" -ForegroundColor Green
    }
}

Write-Host "`nCompleted updating all GitHub Actions to use upload-artifact@v4" -ForegroundColor Green
