# Requirements-to-Code Mapping System
# Creates comprehensive mappings from Requirements → Solutions → Tasks → Code → Tests

param(
    [string]$RequirementsFile = "docs/Requirements/UNIFIED-REQUIREMENTS.md",
    [string]$OutputFile = ".cursor/mappings/requirements-to-code-mapping.md",
    [string]$ReviewDir = ".logs/complete-review"
)

$ErrorActionPreference = "Continue"

Write-Host "=== CREATING REQUIREMENTS-TO-CODE MAPPING ===" -ForegroundColor Cyan
Write-Host ""

# Create review directory
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reviewPath = Join-Path $ReviewDir $timestamp
if (-not (Test-Path $reviewPath)) {
    New-Item -ItemType Directory -Path $reviewPath -Force | Out-Null
}

# Load unified requirements
Write-Host "[1] Loading unified requirements..." -ForegroundColor Yellow
$requirements = Get-Content -Path $requirementsFile -Raw

# Find all solution documents
Write-Host "[2] Finding solution documents..." -ForegroundColor Yellow
$solutions = Get-ChildItem -Path "docs/Solutions", "docs/architecture" -Filter "*.md" -Recurse -ErrorAction SilentlyContinue
Write-Host "  Found $($solutions.Count) solution documents" -ForegroundColor White

# Find all task documents
Write-Host "[3] Finding task documents..." -ForegroundColor Yellow
$tasks = Get-ChildItem -Path "docs/Tasks", "Project-Management" -Filter "*task*.md", "*TASK*.md" -Recurse -ErrorAction SilentlyContinue
Write-Host "  Found $($tasks.Count) task documents" -ForegroundColor White

# Find all code files
Write-Host "[4] Finding code files..." -ForegroundColor Yellow
$codeFiles = @()
$codeFiles += Get-ChildItem -Path "services" -Include "*.py" -Recurse -ErrorAction SilentlyContinue
$codeFiles += Get-ChildItem -Path "unreal/Source" -Include "*.cpp", "*.h" -Recurse -ErrorAction SilentlyContinue
$codeFiles += Get-ChildItem -Path "models" -Include "*.py" -Recurse -ErrorAction SilentlyContinue
Write-Host "  Found $($codeFiles.Count) code files" -ForegroundColor White

# Find all test files
Write-Host "[5] Finding test files..." -ForegroundColor Yellow
$testFiles = Get-ChildItem -Path "tests" -Include "*test*.py", "*spec*.py" -Recurse -ErrorAction SilentlyContinue
Write-Host "  Found $($testFiles.Count) test files" -ForegroundColor White

# Build mapping structure
Write-Host "[6] Building mapping structure..." -ForegroundColor Yellow

$mappingContent = @"
# Requirements-to-Code Mapping
**Generated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  
**Requirements File**: $RequirementsFile  
**Total Requirements**: [To be populated]  
**Total Code Files**: $($codeFiles.Count)  
**Total Test Files**: $($testFiles.Count)

---

## MAPPING STRUCTURE

```
Requirement ID (REQ-XXX)
  └─> Solution Document (solution-xxx.md)
      └─> Task ID (TASK-XXX)
          └─> Code Files:
              ├─> path/to/code.py (lines X-Y) - Description
              └─> path/to/code.cpp (lines X-Y) - Description
          └─> Test Files:
              ├─> path/to/test.py (lines X-Y) - Test type
              └─> path/to/test.py (lines X-Y) - Test type
```

---

## MAPPING STATUS CODES

- ✅ **COMPLETE**: Requirement → Solution → Tasks → Code → Tests (all present)
- ⚠️ **PARTIAL**: Some links missing (document what's missing)
- ❌ **MISSING**: Major components missing (solution, code, or tests)
- 🔴 **FAIL**: Fake/mock code detected

---

## DETAILED MAPPINGS

"@

# Extract requirements from unified document
$reqPattern = '(?m)^(?:#{1,3}|REQ-|REQUIREMENT|##\s+)(.+?)(?:\s|$)'
$reqMatches = [regex]::Matches($requirements, $reqPattern)

$reqCount = 0
foreach ($match in $reqMatches) {
    $reqTitle = $match.Groups[1].Value.Trim()
    if ($reqTitle -match '^(TABLE|CORE|TECHNICAL|AI|PLATFORM|MONETIZATION|USER|CONTENT|PERFORMANCE|COST|MODEL|TERRAIN|WEATHER|DAY|FACIAL|VOICE|IMMERSIVE|STORY|UE5|PEER|CODE)' -and $reqTitle.Length -gt 5) {
        $reqCount++
        $reqId = "REQ-$($reqCount.ToString('D3'))"
        
        $mappingContent += "`n`n## ${reqId}: $reqTitle`n`n"
        $mappingContent += "**Status**: ⚠️ PARTIAL (mapping in progress)`n`n"
        $mappingContent += "### Solutions:`n"
        $mappingContent += "- [To be mapped]`n`n"
        $mappingContent += "### Tasks:`n"
        $mappingContent += "- [To be mapped]`n`n"
        $mappingContent += "### Code Files:`n"
        $mappingContent += "- [To be mapped]`n`n"
        $mappingContent += "### Test Files:`n"
        $mappingContent += "- [To be mapped]`n`n"
    }
}

$mappingContent = $mappingContent -replace '\[To be populated\]', $reqCount

# Save mapping
$mappingContent | Set-Content -Path $OutputFile -Encoding UTF8
Write-Host "[OK] Mapping structure created: $OutputFile" -ForegroundColor Green

# Also save to review directory
$reviewOutput = Join-Path $reviewPath "mapping-initial.md"
$mappingContent | Set-Content -Path $reviewOutput -Encoding UTF8
Write-Host "[OK] Review copy saved: $reviewOutput" -ForegroundColor Green

Write-Host ""
Write-Host "=== MAPPING STRUCTURE CREATED ===" -ForegroundColor Green
Write-Host "  Requirements identified: $reqCount" -ForegroundColor White
Write-Host "  Code files: $($codeFiles.Count)" -ForegroundColor White
Write-Host "  Test files: $($testFiles.Count)" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Next step: Populate mappings with actual code/test connections" -ForegroundColor Yellow

