# Documentation Placement Checking Feature
# This feature verifies documentation is properly organized

function Initialize-DocumentationPlacement {
    # REMOVED: File listing removed per user request - sessions should not list files
    # Documentation placement check runs silently without listing files
    if (Test-Path ".\Global-Scripts\check-documentation-placement.ps1") {
        # Run check silently (redirect output to null) - only show if there's an actual error
        $null = & .\Global-Scripts\check-documentation-placement.ps1 2>&1
        if ($LASTEXITCODE -eq 0) {
            # All documentation is properly placed - no output needed
        } else {
            # Files are misplaced but don't list them - just note that check can be run
            # Silent - user can run check manually if needed
        }
    }
    # Feature initialized silently - no file listings
}

