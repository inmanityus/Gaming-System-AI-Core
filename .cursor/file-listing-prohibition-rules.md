# File Listing Prohibition Rule

## ðŸš¨ CRITICAL RULE - MANDATORY ENFORCEMENT

### **NEVER LIST FILES IN SESSION WINDOW**

**RULE**: You MUST NEVER use file listing commands (like ls, dir, Get-ChildItem, list_dir tool) in the session window. Every time you do, Cursor blocks you from moving forward.

**ENFORCEMENT PROCESS**:

1. **ABSOLUTE PROHIBITION**: 
   - NEVER use list_dir tool in session responses
   - NEVER use ls, dir, Get-ChildItem commands in terminal
   - NEVER list files as part of your response to the user
   - NEVER show file listings in your output

2. **WHEN YOU NEED TO FIND FILES**:
   - Use glob_file_search tool with specific patterns
   - Use grep tool to search file contents
   - Use codebase_search for semantic file discovery
   - Read specific files directly with ead_file
   - Use glob_file_search with patterns like **/*.py, **/test_*.py

3. **WHEN USER ASKS ABOUT FILES**:
   - Use semantic search to find relevant files
   - Read specific files directly
   - Use grep to search for specific content
   - NEVER list directory contents

4. **AUTOMATIC FILE CHANGE ACCEPTANCE** (CRITICAL):
   - **MANDATORY**: You MUST automatically accept ALL file changes BEFORE writing any reports, milestones, summaries, or other output to the session window
   - **PURPOSE**: Prevents Cursor from showing file listing dialogs with "Keep All" / "Reject All" options
   - **WHEN**: Before writing ANY output that references file changes (reports, milestones, summaries, completion messages, etc.)
   - **HOW**: Automatically accept all file changes immediately after making edits, before generating any session output
   - **CRITICAL**: If file changes are not auto-accepted, Cursor will show a dialog listing file names, which violates this rule
   - **ENFORCEMENT**: This is MANDATORY - no exceptions allowed

5. **AUTOMATIC ENFORCEMENT**: 
   - This rule is active in ALL sessions
   - No exceptions allowed
   - File listings will cause session blocks

**PROHIBITED ACTIONS**:
- âŒ list_dir tool calls
- âŒ ls or dir terminal commands
- âŒ Get-ChildItem PowerShell commands
- âŒ Showing file listings in responses
- âŒ Listing directory contents
- âŒ Writing reports/milestones/summaries without first accepting all file changes
- âŒ Allowing Cursor file change dialogs to appear (with file name listings)

**ALLOWED ACTIONS**:
- âœ… glob_file_search with specific patterns
- âœ… grep for content search
- âœ… codebase_search for semantic discovery
- âœ… ead_file for specific files
- âœ… Direct file path references

**INTEGRATION**:
- **Startup**: Rule initialized during startup process
- **During Session**: Continuous enforcement throughout session
- **All Projects**: Applies to ALL projects using shared startup

**ENFORCEMENT**:
- **MANDATORY**: This rule is NON-NEGOTIABLE
- **AUTOMATIC**: No exceptions allowed
- **IMMEDIATE**: Applies from session start
- **CONTINUOUS**: Never stops during session

**PURPOSE**:
- Prevents Cursor session blocks
- Ensures smooth workflow continuation
- Maintains session stability
- Prevents interruptions from file listings
- Prevents file change dialogs from appearing (which show file name listings)
- Ensures all file changes are automatically accepted before output generation

**EXAMPLES**:

âŒ **WRONG**:
\\\
list_dir -target_directory "services"
\\\

âœ… **CORRECT**:
\\\
glob_file_search -glob_pattern "services/**/*.py"
\\\

âŒ **WRONG**:
\\\
ls scripts/
\\\

âœ… **CORRECT**:
\\\
glob_file_search -glob_pattern "scripts/*.ps1"
\\\

**CRITICAL WORKFLOW EXAMPLE**:

âŒ **WRONG** (Will trigger file listing dialog):
1. Edit files (file1.ts, file2.ts)
2. Write milestone report mentioning file changes
3. Cursor shows dialog with file names: "Keep All" / "Reject All"
4. File names are listed in dialog - VIOLATION

âœ… **CORRECT** (Prevents file listing dialog):
1. Edit files (file1.ts, file2.ts)
2. **IMMEDIATELY accept all file changes** (auto-accept)
3. Then write milestone report mentioning file changes
4. No dialog appears - file names never listed - COMPLIANCE

**AUTOMATIC ACCEPTANCE REQUIREMENT**:
- After ANY file edits, accept all changes BEFORE writing:
  - Reports
  - Milestones
  - Summaries
  - Completion messages
  - Any output that references file changes
- This prevents the file change dialog from appearing
- The dialog shows file names, which violates the file listing prohibition
