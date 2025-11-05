# Requirements Consolidation Script
# Merges all requirements documents, newer files override older when clashing

param(
    [string]$OutputFile = "docs/Requirements/UNIFIED-REQUIREMENTS.md",
    [string]$ReviewDir = ".logs/complete-review"
)

$ErrorActionPreference = "Continue"

Write-Host "=== REQUIREMENTS CONSOLIDATION ===" -ForegroundColor Cyan
Write-Host ""

# Create review directory if needed
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reviewPath = Join-Path $ReviewDir $timestamp
if (-not (Test-Path $reviewPath)) {
    New-Item -ItemType Directory -Path $reviewPath -Force | Out-Null
}

# Find all requirements documents
$requirementsFiles = Get-ChildItem -Path "docs/Requirements" -Filter "*.md" -File | 
    Sort-Object LastWriteTime -Descending

Write-Host "Found $($requirementsFiles.Count) requirements documents:" -ForegroundColor Yellow
$requirementsFiles | ForEach-Object {
    Write-Host "  - $($_.Name) ($($_.LastWriteTime.ToString('yyyy-MM-dd')))" -ForegroundColor White
}

Write-Host ""
Write-Host "Consolidating requirements (newer files override older)..." -ForegroundColor Yellow

# Build unified requirements document
$unifiedContent = @"
# Unified Requirements Document
**Project**: "The Body Broker" - AI-Driven Horror Game  
**Consolidated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  
**Source Files**: $($requirementsFiles.Count) documents  
**Consolidation Rule**: Newer files override older when requirements clash

---

## TABLE OF CONTENTS

1. [Core Vision & Game Concept](#core-vision--game-concept)
2. [Technical Architecture](#technical-architecture)
3. [AI System Requirements](#ai-system-requirements)
4. [Platform & Deployment](#platform--deployment)
5. [Monetization System](#monetization-system)
6. [User Experience Requirements](#user-experience-requirements)
7. [Content Rating & Safety](#content-rating--safety)
8. [Performance Requirements](#performance-requirements)
9. [Cost Targets](#cost-targets)
10. [Model Architecture Requirements](#model-architecture-requirements)
11. [Model Training Requirements](#model-training-requirements)
12. [Multi-Language Speech System](#multi-language-speech-system)
13. [Terrain System Requirements](#terrain-system-requirements)
14. [Weather System Requirements](#weather-system-requirements)
15. [Day/Night World Requirements](#daynight-world-requirements)
16. [Facial Expression Requirements](#facial-expression-requirements)
17. [Voice & Audio Requirements](#voice--audio-requirements)
18. [Immersive Features Requirements](#immersive-features-requirements)
19. [Story Teller Requirements](#story-teller-requirements)
20. [UE5 Tools Requirements](#ue5-tools-requirements)
21. [Peer Coding & Pairwise Testing Requirements](#peer-coding--pairwise-testing-requirements)
22. [Code Quality & Audit Requirements](#code-quality--audit-requirements)

---

## PEER CODING & PAIRWISE TESTING REQUIREMENTS

**MANDATORY - NO EXCEPTIONS**

### Core Principle
**ALL code must be peer-reviewed and ALL tests must be pairwise-validated. This is not optional.**

### Peer-Based Coding Requirements

**MANDATORY PROCESS:**
1. **Coder Model** (Primary): Writes code implementation
   - Must meet minimum model levels (Claude 4.5+, GPT-5+, Gemini 2.5 Pro+)
   - Implements requirement based on unified requirements document
   - Ensures code is real, not mock/fake/placeholder
   
2. **Reviewer Model** (Secondary): Reviews code
   - Must be different model from different provider when possible
   - Must meet minimum model levels
   - Validates:
     - Code is real and not mock/fake
     - Code is syntactically correct
     - Code is optimized while supporting requirements
     - Code meets all requirement specifications
   
3. **Coder Final Review**: Coder reviews Reviewer feedback
   - Ensures Reviewer feedback is incorporated
   - Verifies code is real and not mock/fake
   - Verifies code is syntactically correct
   - Optimizes code while supporting requirements
   - Adds code to file

**AUDIT TRAIL REQUIREMENTS:**
- Every code file MUST have audit trail document
- Audit trail must include:
  - Coder model name and version
  - Reviewer model name and version
  - Review timestamp
  - Review feedback summary
  - Changes made based on review
  - Final approval status

### Pairwise Testing Requirements

**MANDATORY PROCESS:**
1. **Tester Model** (Primary): Creates tests
   - Must meet minimum model levels
   - Writes comprehensive test suite
   - Tests cover all code paths, edge cases, error conditions
   
2. **Reviewer Model** (Secondary): Validates tests
   - Must be different model from different provider
   - Must meet minimum model levels
   - Validates:
     - Tests are real and test real code (not mocks in integration+ tests)
     - Tests properly test the code
     - Tests enforce requirements
     - Tests cover edge cases
   
3. **Tester Final Review**: Tester reviews Reviewer feedback
   - Verifies tests are correct
   - Verifies tests properly test the code
   - Adds tests to testing suite

**TEST EXECUTION REQUIREMENTS:**
1. **Tester Model**: Runs all tests
   - Runs test suite
   - Captures all results
   
2. **Reviewer Model**: Runs same tests independently
   - Runs identical test suite
   - Compares results to Tester
   - Non-matches are rejected and force test re-write
   
3. **Iteration**: Process repeats until all tests pass and results match

**AUDIT TRAIL REQUIREMENTS:**
- Every test file MUST have audit trail document
- Audit trail must include:
  - Tester model name and version
  - Reviewer model name and version
  - Test execution timestamp
  - Test results from both models
  - Result comparison
  - Final validation status

**TEST HIERARCHY REQUIREMENTS:**
- Unit Tests: Test individual functions/methods (mocked dependencies OK for unit tests only)
- Functional Tests: Test functional units (groups of functions)
- Integration Tests: Test component integration (NO mocks - real implementations)
- Subsystem Tests: Test complete subsystems
- System Tests: Test complete system functionality
- Cross-System Tests: Test interactions between systems
- E2E Tests: Test complete user journeys

### Minimum Model Levels

**MANDATORY - NO EXCEPTIONS:**
- Claude: Minimum 4.5 Sonnet, 4.1 Opus (NO Claude 3.x allowed)
- GPT: Minimum 5, 5-Pro, Codex-2 (NO GPT-4.0, GPT-4o, GPT-3.x allowed)
- Gemini: Minimum 2.5 Pro or 2.5 Flash (NO Gemini 1.5 allowed)
- DeepSeek: Minimum V3 (3.1 Terminus) (NO V2 or V1 allowed)
- Grok: Minimum 4 or 4 Fast (NO Grok 3.x allowed)
- Mistral: Minimum 3.1 Medium or Devstral (NO 1.x allowed)

**Reference**: `Global-Workflows/minimum-model-levels.md`

### Enforcement

**MANDATORY ENFORCEMENT:**
- ❌ NO code without peer review
- ❌ NO tests without pairwise validation
- ❌ NO older generation models
- ❌ NO skipping audit trails
- ❌ NO mock/fake code in production paths
- ❌ NO static test examples

**AUDIT TRAIL LOCATION:**
- Code audit trails: `.cursor/audit/code/[filename]-audit.md`
- Test audit trails: `.cursor/audit/tests/[testname]-audit.md`
- Consolidated audit index: `.cursor/audit/index.md`

---

"@

# Process each requirements file (newest first, so newer content overrides older)
$processedSections = @{}
foreach ($file in $requirementsFiles) {
    Write-Host "Processing: $($file.Name)" -ForegroundColor Cyan
    $content = Get-Content -Path $file.FullName -Raw
    
    # Extract sections (marked by ## or ###)
    $sectionMatches = [regex]::Matches($content, '(?m)^(#{2,3})\s+(.+)$')
    
    foreach ($match in $sectionMatches) {
        $sectionLevel = $match.Groups[1].Value.Length
        $sectionTitle = $match.Groups[2].Value.Trim()
        
        # Extract section content
        $sectionStart = $match.Index
        $nextSection = $sectionMatches | Where-Object { $_.Index -gt $sectionStart } | Select-Object -First 1
        $sectionEnd = if ($nextSection) { $nextSection.Index } else { $content.Length }
        $sectionContent = $content.Substring($sectionStart, $sectionEnd - $sectionStart).Trim()
        
        # Store section (newer files override)
        $sectionKey = $sectionTitle.ToLower() -replace '[^\w\s]', '' -replace '\s+', '-'
        $processedSections[$sectionKey] = @{
            Title = $sectionTitle
            Level = $sectionLevel
            Content = $sectionContent
            Source = $file.Name
            Date = $file.LastWriteTime
        }
    }
}

# Add processed sections to unified document
$unifiedContent += "`n`n---`n`n"
foreach ($section in $processedSections.Values | Sort-Object Title) {
    $unifiedContent += "$('#' * $section.Level) $($section.Title)`n`n"
    $unifiedContent += "*Source: $($section.Source) ($($section.Date.ToString('yyyy-MM-dd')))*`n`n"
    $unifiedContent += "$($section.Content)`n`n`n"
}

# Save unified requirements
$unifiedContent | Set-Content -Path $OutputFile -Encoding UTF8
Write-Host "[OK] Unified requirements saved: $OutputFile" -ForegroundColor Green

# Also save to review directory
$reviewOutput = Join-Path $reviewPath "unified-requirements.md"
$unifiedContent | Set-Content -Path $reviewOutput -Encoding UTF8
Write-Host "[OK] Review copy saved: $reviewOutput" -ForegroundColor Green

Write-Host ""
Write-Host "=== CONSOLIDATION COMPLETE ===" -ForegroundColor Green
Write-Host "  Sections consolidated: $($processedSections.Count)" -ForegroundColor White
Write-Host "  Output: $OutputFile" -ForegroundColor White

