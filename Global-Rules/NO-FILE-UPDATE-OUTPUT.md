# Global Rule: No File Update Output

## CRITICAL RULE

**NEVER output file creation/update notifications in the session window.**

### Why
- File update messages cause session stalls
- They create excessive output that slows down the session
- The user can see file changes in the editor/IDE
- Progress should be shown through status updates, not file listings

### What NOT to Output
- ❌ "Created file: path/to/file.ts"
- ❌ "Updated file: path/to/file.ts"
- ❌ "Wrote contents to: path/to/file.ts"
- ❌ Lists of "Files Created:" or "Files Updated:"
- ❌ Any file path outputs in status messages

### What TO Output Instead
- ✅ Status updates: "✓ Task X complete"
- ✅ Progress percentages: "Progress: 6/25 tasks (24%)"
- ✅ Milestone completion: "Milestone 6: API Gateway ✅"
- ✅ Test results: "All tests passing ✅"
- ✅ Commands executed (when relevant)
- ✅ Essential progress information only

### Exception
- Only mention specific files when:
  - User explicitly asks about a file
  - File location is critical for user action (e.g., "Configuration saved to config.yaml")
  - Error occurs related to a specific file

## Implementation

**This rule applies to ALL sessions across ALL projects.**

When creating or updating files:
1. Use the write/search_replace tools silently
2. Show only high-level status updates
3. Never echo file paths in progress messages
4. Continue working without file update notifications

**Status:** Active  
**Priority:** High  
**Applies To:** All AI sessions  
**Enforcement:** Immediate

