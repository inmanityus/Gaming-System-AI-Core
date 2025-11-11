# Conservative Project-Specific File Handling

**Version:** 1.0  
**Last Updated:** October 22, 2025  
**Status:** Active  

## Overview

This document outlines the conservative approach for handling project-specific files during global resource synchronization. The approach prioritizes maintaining clean, universal deployment folders while being very selective about generalization.

## Core Principles

### 1. Conservative Generalization
- **Default Action:** Delete project-specific content
- **Generalization Threshold:** Only generalize if truly universal patterns exist
- **Evidence Required:** Must demonstrate clear reusability across multiple project types

### 2. File Type Handling

#### Images (Automatic Deletion)
**Rule:** All project-specific images are automatically deleted
**Rationale:** Images are inherently project-specific and rarely generalize well
**File Extensions:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.bmp`, `.ico`

**Examples:**
- `bff-network-final-with-trainer-tips.png` → **DELETE**
- `trainer-cards-view.png` → **DELETE**
- `for-trainers-page.png` → **DELETE**

#### Other Files (Conservative Evaluation)
**Rule:** Evaluate for potential generalization, but be very conservative
**Criteria:** Must contain truly universal patterns applicable across different project types

**Evaluation Questions:**
1. Does this file contain patterns that would be useful for ANY project type?
2. Is the content generic enough to apply to non-fitness projects?
3. Would this be valuable for projects in completely different domains?

**Examples:**
- `setup-personal-training-system.ps1` → **EVALUATE** (may contain universal PowerShell patterns)
- `project-config-template.json` → **EVALUATE** (may contain universal configuration patterns)
- `database-schema-template.sql` → **EVALUATE** (may contain universal database patterns)

## Generalization Process

### Step 1: Identify Universal Patterns
Look for patterns that transcend project domains:
- Generic PowerShell automation patterns
- Universal configuration templates
- Common database schema patterns
- Reusable API patterns
- Generic deployment scripts

### Step 2: Extract and Abstract
- Remove all project-specific references
- Replace specific values with placeholders
- Add comprehensive documentation
- Include usage examples

### Step 3: Document in Global-Docs
- Create clear, generic documentation
- Provide multiple usage examples
- Include customization guidelines
- Add troubleshooting information

## Anti-Patterns (Avoid These)

### ❌ Over-Generalization
- Trying to make everything "universal"
- Creating overly complex abstraction layers
- Forcing project-specific content into generic templates

### ❌ Premature Generalization
- Generalizing before seeing patterns across multiple projects
- Creating "universal" solutions based on single project experience
- Assuming patterns will be useful without evidence

### ❌ Project-Specific Leakage
- Leaving project-specific references in "universal" templates
- Including domain-specific terminology
- Creating templates that only work for specific project types

## Implementation in Sync-Deployment Script

### Image File Handling
```powershell
# Automatically delete image files
$imageFiles = $allFiles | Where-Object { 
    $_.Extension -match "\.(png|jpg|jpeg|gif|svg|webp|bmp|ico)$" 
}
if ($imageFiles.Count -gt 0) {
    $imageFiles | Remove-Item -Force
    Write-Host "✅ Deleted $($imageFiles.Count) project-specific image files"
}
```

### Other File Evaluation
```powershell
# Flag other files for potential generalization
$otherProjectFiles = $allFiles | Where-Object {
    $_.Extension -notmatch "\.(png|jpg|jpeg|gif|svg|webp|bmp|ico)$" -and (
        $_.Name -match "(project-specific-patterns)" -or
        $_.Content -match "(project-specific-content)"
    )
}
if ($otherProjectFiles.Count -gt 0) {
    Write-Host "📄 Found other project-specific files (evaluate for generalization)"
    Write-Host "Conservative approach: Only generalize if truly universal patterns exist"
}
```

## Decision Framework

### When to Generalize
✅ **Generalize When:**
- Pattern appears in 3+ different project types
- Content is domain-agnostic
- Clear reusability across different industries
- Well-documented and tested

### When to Delete
❌ **Delete When:**
- Project-specific images or assets
- Domain-specific content (fitness, healthcare, etc.)
- Single-use scripts or configurations
- Content tied to specific business logic

## Examples

### Good Generalization Candidates
1. **PowerShell Script Templates**
   - Generic file processing patterns
   - Universal deployment automation
   - Common system administration tasks

2. **Configuration Templates**
   - Generic environment variable patterns
   - Universal database connection templates
   - Common API configuration patterns

3. **Documentation Templates**
   - Generic project setup guides
   - Universal deployment procedures
   - Common troubleshooting patterns

### Poor Generalization Candidates
1. **Project-Specific Images**
   - Brand logos and graphics
   - Domain-specific screenshots
   - Project-specific diagrams

2. **Business Logic Scripts**
   - Fitness-specific calculations
   - Domain-specific data processing
   - Industry-specific workflows

3. **Project-Specific Configurations**
   - Hardcoded project values
   - Domain-specific settings
   - Single-project optimizations

## Benefits of Conservative Approach

### 1. Clean Deployment Folders
- No project-specific clutter
- Universal templates only
- Easy to understand and use

### 2. High-Quality Generalizations
- Only truly useful patterns are generalized
- Well-tested and documented
- Clear value proposition

### 3. Reduced Maintenance
- Fewer files to maintain
- Less risk of outdated generalizations
- Focus on high-value patterns

### 4. Better User Experience
- Clear separation between universal and project-specific
- No confusion about what's reusable
- Easy to find relevant templates

## Monitoring and Review

### Regular Review Process
1. **Monthly Review:** Evaluate flagged files for generalization potential
2. **Pattern Analysis:** Look for recurring patterns across projects
3. **Usage Tracking:** Monitor which generalizations are actually used
4. **Cleanup:** Remove unused or outdated generalizations

### Success Metrics
- **Clean Deployment Folders:** Zero project-specific files
- **High-Quality Generalizations:** Only truly universal patterns
- **User Satisfaction:** Easy to find and use relevant templates
- **Maintenance Efficiency:** Minimal overhead for generalization maintenance

## Related Documentation

- **Sync-Deployment Script:** Implementation details
- **Global-Docs Structure:** Where generalizations are stored
- **Project Memory System:** How patterns are identified and documented
- **Deployment Folder Structure:** Organization of universal resources

---

**Status:** Active  
**Priority:** High  
**Applies To:** All projects using sync-deployment  
**Enforcement:** Automatic via sync-deployment script
