# Memory Structure Setup Feature
# This feature creates and manages the AI session memory structure

function Initialize-MemoryStructure {
    Write-Host ""
    Write-Host "Checking Memory Structure for Optimal AI Sessions..." -ForegroundColor Yellow
    $memoryStructureExists = Test-Path ".cursor/memory"
    if (-not $memoryStructureExists) {
        Write-Host "[MEMORY] Creating memory structure for long-running AI sessions..." -ForegroundColor Cyan
        
        # Auto-detect project name from current directory
        $projectRoot = Split-Path -Leaf (Get-Location)
        $projectName = $projectRoot
        
        # Create directories
        New-Item -Path ".cursor/memory/active" -ItemType Directory -Force | Out-Null
        New-Item -Path ".cursor/memory/archive/decisions" -ItemType Directory -Force | Out-Null
        New-Item -Path ".cursor/memory/archive/$(Get-Date -Format yyyy-MM)" -ItemType Directory -Force | Out-Null
        
        # Create memory files with templates
        @"
# Project Brief: $projectName

## Purpose
[Document what this project does - AI will help populate this]

## Core Requirements
- [Add key requirements as they emerge]

## Constraints
- [Add constraints]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/PROJECT_BRIEF.md" -Encoding UTF8
        
        @"
# Technology Stack: $projectName

## Frontend
- **Framework:** [e.g., Next.js]
- **Language:** [e.g., TypeScript]

## Backend
- **Framework:** [e.g., Express]
- **Database:** [e.g., PostgreSQL]

## Key Libraries
[Add major dependencies as they're used]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/TECH_STACK.md" -Encoding UTF8
        
        @"
# Architecture: $projectName

## Key Architectural Decisions
[Document major decisions as you make them]

## Patterns Used
[Add patterns as they emerge]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/ARCHITECTURE.md" -Encoding UTF8
        
        @"
# Coding Patterns: $projectName

## Conventions
[Document coding standards as they emerge]

## File Naming
[Add conventions]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/PATTERNS.md" -Encoding UTF8
        
        @"
# Current Focus
**Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## What We're Working On
[Update with current task - AI will maintain this]

## Status
[Current state]
"@ | Out-File -FilePath ".cursor/memory/active/CURRENT_FOCUS.md" -Encoding UTF8
        
        @"
# Active Work
**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Current Feature
[Update with current feature - AI will maintain this]

## Completed Today
- [Add completed items]

## Next Steps
- [ ] [Add next tasks]
"@ | Out-File -FilePath ".cursor/memory/active/ACTIVE_WORK.md" -Encoding UTF8
        
        @"
# Recent Decisions
**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## This Week
[Add recent decisions - AI will maintain this]
"@ | Out-File -FilePath ".cursor/memory/active/RECENT_DECISIONS.md" -Encoding UTF8
        
        Write-Host "[SUCCESS] Memory structure created!" -ForegroundColor Green
        Write-Host "   [LOCATION] Location: .cursor/memory/" -ForegroundColor White
        Write-Host "   [BENEFIT] Benefits: 3-5x longer AI sessions, 70-90% less context usage" -ForegroundColor White
        Write-Host "   [ACTION] Action: Populate PROJECT_BRIEF.md and TECH_STACK.md with project details" -ForegroundColor Yellow
        Write-Host "   [GUIDE] Guide: See Global-Workflows/Memory-Structure-Setup-Guide.md" -ForegroundColor Gray
        
        # Add to .gitignore automatically
        if (Test-Path ".gitignore") {
            $gitignoreContent = Get-Content ".gitignore" -Raw -ErrorAction SilentlyContinue
            if ($gitignoreContent -notmatch "\.cursor/memory/") {
                Write-Host "   [ACTION] Adding .cursor/memory/ to .gitignore..." -ForegroundColor Yellow
                @"

# AI Session Memory (auto-created by startup.ps1)
# These files are session-specific and should not be committed
.cursor/memory/
"@ | Add-Content ".gitignore" -Encoding UTF8
                Write-Host "   [OK] Added to .gitignore" -ForegroundColor Green
            }
        }
    } else {
        # Memory structure exists, check if files are populated
        $briefSize = if (Test-Path ".cursor/memory/PROJECT_BRIEF.md") { 
            (Get-Item ".cursor/memory/PROJECT_BRIEF.md").Length 
        } else { 0 }
        
        if ($briefSize -lt 200) {
            Write-Host "[WARNING] Memory structure exists but needs population" -ForegroundColor Yellow
            Write-Host "   [ACTION] Action: Populate .cursor/memory/PROJECT_BRIEF.md with project details" -ForegroundColor Yellow
            Write-Host "   [GUIDE] Guide: See Global-Workflows/Memory-Structure-Setup-Guide.md" -ForegroundColor Gray
        } else {
            Write-Host "[OK] Memory structure ready - AI sessions optimized" -ForegroundColor Green
            Write-Host "   [LOCATION] Location: .cursor/memory/" -ForegroundColor White
            Write-Host "   [UPDATE] Update: ACTIVE_WORK.md and CURRENT_FOCUS.md as you work" -ForegroundColor Gray
        }
    }
}

