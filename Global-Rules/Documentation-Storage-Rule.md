# Documentation Storage Rule

## Overview
All project documentation, session summaries, and status reports MUST be stored in designated folders that are excluded from deployment and version control.

## The Golden Rule

**📝 NEVER place documentation in website/application folders that get deployed!**

Documentation must be separated from code to:
- Prevent documentation from being deployed to production
- Keep codebase clean and focused
- Avoid accidental exposure of internal information
- Maintain clear separation of concerns

## Standard Documentation Structure

Every project MUST have a `Project-Management/` folder (or similar) that contains:

```
Project-Management/
├── Documentation/          # All .md files, guides, protocols
├── Research/              # Research notes, planning documents
├── AWS-Deployment/        # Deployment logs, status reports
├── Media-Source/          # Source media files (before optimization)
├── Archive/               # Deprecated files, old artifacts
└── Scripts/               # Project management scripts (non-production)
```

## Implementation

### 1. Create Project-Management Folder

```powershell
# PowerShell
New-Item -ItemType Directory -Path "Project-Management" -Force
New-Item -ItemType Directory -Path "Project-Management/Documentation" -Force
New-Item -ItemType Directory -Path "Project-Management/AWS-Deployment" -Force
New-Item -ItemType Directory -Path "Project-Management/Archive" -Force
```

### 2. Add to .gitignore

**Root `.gitignore`:**
```gitignore
# Project Management and Documentation (not for deployment)
Project-Management/
.aws-deployment/
.playwright-mcp/

# Development artifacts
*.log
*.log.json
*-SUMMARY.md
*-STATUS.md
*-COMPLETE.md
SESSION-*.md
```

**Application-specific `.gitignore` (if separate folder):**
```gitignore
# Session/status documentation (keep in Project-Management)
*-SUMMARY.md
*-STATUS.md
*-COMPLETE.md
SESSION-*.md
*-FIX-*.md
*-IMPLEMENTATION-*.md
PROJECT-MANAGEMENT/
```

### 3. Update Deployment Scripts

Ensure deployment scripts exclude documentation:

```bash
# rsync example
rsync -avz --exclude 'Project-Management/' --exclude '.git/' ./app/ server:/var/www/app/

# npm/next.js example (next.config.js)
module.exports = {
  output: 'standalone',
  // Only includes necessary files for production
}
```

## File Naming Conventions

### Documentation Files (Project-Management/)

**✅ CORRECT:**
- `DEPLOYMENT-STATUS-HANDOFF.md`
- `SESSION-SUMMARY-2025-10-14.md`
- `FEATURE-IMPLEMENTATION-COMPLETE.md`
- `PROJECT-STATUS-UPDATE.md`

**Location**: `Project-Management/Documentation/` or `Project-Management/AWS-Deployment/`

### Code Documentation (can stay in app)

**✅ CORRECT:**
- `README.md` (project overview)
- `CONTRIBUTING.md` (for contributors)
- `API.md` (API reference)
- `QUICK-START.md` (setup guide)

**Location**: Root or in application folder, but these should be minimal and focused

## Automated Checks

Use the provided script to verify documentation placement:

```powershell
# Run documentation placement check
.\Global-Scripts\check-documentation-placement.ps1

# Output shows any misplaced documentation files
```

## Migration Guide

If documentation is currently in the wrong place:

1. **Create Project-Management structure**
2. **Move all session/status files**:
   ```powershell
   Move-Item -Path "*-SUMMARY.md" -Destination "Project-Management/Documentation/"
   Move-Item -Path "*-STATUS.md" -Destination "Project-Management/Documentation/"
   Move-Item -Path "SESSION-*.md" -Destination "Project-Management/Documentation/"
   ```
3. **Update .gitignore**
4. **Update references** in README.md
5. **Commit changes**

## Verification

Before any deployment:

1. ✅ Check no `*-SUMMARY.md`, `*-STATUS.md` files in application folders
2. ✅ Verify `Project-Management/` is in `.gitignore`
3. ✅ Ensure deployment script excludes documentation
4. ✅ Test build to confirm no documentation included

## Exception: User-Facing Documentation

Some documentation MAY remain in the application if:
- It's intended for end users (e.g., help pages)
- It's required for the application to function
- It's part of a documentation site being deployed

**Examples that CAN stay in app:**
- `/docs/` folder for a documentation website
- `/help/` pages served to users
- Inline code documentation

**But still move to Project-Management:**
- Development session notes
- Deployment status reports
- Internal planning documents
- Research and analysis

## Startup Verification

Add this check to your `startup.ps1` or equivalent:

```powershell
# Check for misplaced documentation
$misplacedDocs = Get-ChildItem -Path "functional-fitness-website" -Filter "*-SUMMARY.md" -Recurse -ErrorAction SilentlyContinue
if ($misplacedDocs) {
    Write-Host "⚠️  WARNING: Found documentation files in application folder!" -ForegroundColor Yellow
    $misplacedDocs | ForEach-Object { Write-Host "  - $($_.FullName)" -ForegroundColor Yellow }
    Write-Host "  Move these to Project-Management/Documentation/" -ForegroundColor Yellow
}
```

## Related Scripts

- `Global-Scripts/check-documentation-placement.ps1` - Verify doc placement
- `Global-Scripts/move-documentation.ps1` - Migrate docs to correct location
- `Global-Scripts/create-project-management-structure.ps1` - Setup PM folders

---

**Version**: 1.0  
**Last Updated**: October 2025  
**Applies To**: All projects, especially those with deployment requirements


