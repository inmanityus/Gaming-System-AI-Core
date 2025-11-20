# Simple comprehensive fix for workflow branch names from 'main' to 'master'
Write-Host "Updating GitHub Actions workflows to use 'master' branch..." -ForegroundColor Cyan

$workflowPath = ".github/workflows"
$totalUpdates = 0

Get-ChildItem -Path $workflowPath -Filter "*.yml" | ForEach-Object {
    $file = $_.FullName
    $content = Get-Content $file -Raw
    $originalContent = $content
    
    # Skip files that use trufflesecurity/trufflehog@main
    if ($content -match "trufflehog@main") {
        $content = $content -replace 'branches:\s*\[\s*main', 'branches: [ master'
        $content = $content -replace ',\s*main\s*\]', ', master ]'
        $content = $content -replace ',\s*main\s*,', ', master,'
        $content = $content -replace 'refs/heads/main', 'refs/heads/master'
    } else {
        # For other files, replace all 'main' with 'master'
        $content = $content -replace '\bmain\b', 'master'
    }
    
    if ($content -ne $originalContent) {
        Set-Content -Path $file -Value $content -NoNewline
        Write-Host "  ✅ Updated: $($_.Name)" -ForegroundColor Green
        $totalUpdates++
    }
}

Write-Host "`nUpdated $totalUpdates workflow files" -ForegroundColor Yellow
Write-Host "Workflows will now trigger on 'master' branch pushes" -ForegroundColor Green
