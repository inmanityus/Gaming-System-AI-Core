# Comprehensive fix for workflow branch names from 'main' to 'master'
Write-Host "Comprehensively updating GitHub Actions workflows to use 'master' branch..." -ForegroundColor Cyan

$workflowPath = ".github/workflows"
$totalUpdates = 0

Get-ChildItem -Path $workflowPath -Filter "*.yml" | ForEach-Object {
    $file = $_.FullName
    $content = Get-Content $file -Raw
    $originalContent = $content
    $updates = 0
    
    # Pattern 1: branches arrays
    $content = $content -replace 'branches:\s*\[\s*main\s*\]', 'branches: [ master ]'
    $content = $content -replace 'branches:\s*\[\s*main\s*,', 'branches: [ master,'
    $content = $content -replace ',\s*main\s*\]', ', master ]'
    $content = $content -replace ',\s*main\s*,', ', master,'
    
    # Pattern 2: refs/heads/main
    $content = $content -replace 'refs/heads/main', 'refs/heads/master'
    
    # Pattern 3: branch: main (but not action@main)
    $content = $content -replace '(?<!@)branch:\s*main', 'branch: master'
    
    # Pattern 4: Quoted main in branch contexts (but not in uses: statements)
    $lines = $content -split "`n"
    $newLines = @()
    foreach ($line in $lines) {
        if ($line -notmatch 'uses:.*@main' -and $line -notmatch '__main__' -and $line -notmatch '\.yaml' -and $line -notmatch '\.json') {
            $line = $line -replace '(["''])main(["''])', '$1master$2'
        }
        $newLines += $line
    }
    $content = $newLines -join "`n"
    
    if ($content -ne $originalContent) {
        # Count how many changes were made
        $changes = 0
        for ($i = 0; $i -lt $content.Length; $i++) {
            if ($i -lt $originalContent.Length -and $content[$i] -ne $originalContent[$i]) {
                $changes++
            }
        }
        
        Set-Content -Path $file -Value $content -NoNewline
        Write-Host "  ✅ Updated: $($_.Name)" -ForegroundColor Green
        $totalUpdates++
    }
}

Write-Host "`nUpdated $totalUpdates workflow files" -ForegroundColor Yellow
Write-Host "Workflows will now trigger on 'master' branch pushes" -ForegroundColor Green
