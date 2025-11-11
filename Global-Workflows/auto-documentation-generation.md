# Automatic Documentation Generation Rule

**PURPOSE:** Automatically generate comprehensive markdown documentation in Global-Docs whenever a new complex component, subsystem, or system is successfully built.

**ACTIVATION:** Milestone-based (every 45-60 minutes) OR when completing a significant implementation

---

## When to Generate Documentation

### Trigger Conditions

Generate documentation when ANY of these conditions are met:

1. **New Complex Component Built**
   - Multi-file system with dependencies
   - Reusable across projects
   - Requires specific configuration
   - Has external integrations (APIs, MCP servers, etc.)

2. **New Subsystem Implemented**
   - Database schema changes
   - Authentication/authorization systems
   - Email/notification systems
   - Background job/daemon systems
   - API integrations

3. **Production Deployment Completed**
   - New deployment patterns discovered
   - Configuration lessons learned
   - Troubleshooting steps documented

4. **Major Milestone Reached**
   - Every 45-60 minute milestone
   - End of major feature implementation
   - Successful resolution of complex problem

### DO NOT Document

- Simple utility functions
- Single-purpose scripts
- Temporary fixes or workarounds
- Project-specific business logic
- Minor bug fixes

---

## Documentation Process

### Step 1: Check for Existing Documentation

**Before creating new documentation, ALWAYS check:**

```bash
# Search Global-Docs for related content
grep -r "keyword" C:\Users\kento\.cursor\global-cursor-repo\docs\
```

**Examples:**
- Building email system? → Check `AWS-SES-EMAIL-INTEGRATION.md`
- Creating daemon? → Check `SYSTEMD-DAEMON-SETUP.md`
- MCP server? → Check `EXA-MCP-SERVER-SETUP.md`, `PERPLEXITY-ASK-MCP-SERVER-SETUP.md`

### Step 2: Determine Action

| Situation | Action |
|-----------|--------|
| No related file exists | Create NEW file |
| Related file exists, same topic | UPDATE existing file |
| Related file exists, different approach | ADD section to existing file |
| Multiple related files | MERGE or create INDEX file |

### Step 3: Generate Documentation

**File Location:** `C:\Users\kento\.cursor\global-cursor-repo\docs\YOUR-TOPIC.md`

**Required Sections:**

```markdown
# Title (Descriptive, Title Case)
**Brief Description**

## Overview
- What it is
- Why it exists
- When to use it
- Created date and project

## Architecture
- System diagram (ASCII art)
- Components
- Data flow
- Dependencies

## Prerequisites
- Required software/tools
- API keys/credentials
- Knowledge requirements

## Implementation
- Step-by-step setup
- Code examples
- Configuration files
- Commands

## Usage
- How to use the system
- Common patterns
- Best practices
- Code examples

## Troubleshooting
- Common issues
- Solutions
- Debug steps
- Error messages

## Related Documentation
- Links to other Global-Docs files
- External resources

---
**Last Updated:** YYYY-MM-DD
**Maintained By:** AI Development Team
```

### Step 4: Update or Merge

**If updating existing file:**

1. Add date-stamped section for new content:
```markdown
### Update: October 19, 2025

**New Feature:** Added support for...

**Changes:**
- Modified configuration to...
- Added new function...
```

2. Update "Last Updated" footer

3. Add to changelog if file has one

**If merging files:**

1. Create unified structure
2. Combine overlapping sections
3. Maintain all unique content
4. Add migration notes

---

## Documentation Standards

### File Naming

**Format:** `TOPIC-NAME-IN-CAPS.md`

**Examples:**
- `AWS-SES-EMAIL-INTEGRATION.md`
- `SYSTEMD-DAEMON-SETUP.md`
- `EXA-MCP-SERVER-SETUP.md`
- `MULTI-TENANT-DEPLOYMENT.md`
- `AI-COLLABORATIVE-AUTHORING-SYSTEM.md`

**Naming Rules:**
- ALL CAPS with hyphens
- Descriptive, not generic
- Include technology if specific (e.g., `AWS-`, `POSTGRESQL-`)
- Avoid abbreviations unless widely known

### Content Quality

**Required Elements:**

1. **Clear Purpose Statement**
   - First paragraph explains what this is
   - Second paragraph explains why it exists

2. **Practical Examples**
   - Real code snippets (not pseudo-code)
   - Actual commands that work
   - Copy-paste ready

3. **Complete Configuration**
   - All environment variables
   - All config files
   - All commands in sequence

4. **Troubleshooting Section**
   - Real errors encountered
   - Actual solutions that worked
   - Debug steps

5. **Cross-References**
   - Link to related docs
   - Mention dependencies
   - Reference source projects

### Code Block Standards

**Always include language identifier:**

```typescript
// ✅ Good
export function example() {
  return "formatted";
}
```

```
// ❌ Bad - no language specified
function example() {
  return "unformatted";
}
```

**Use appropriate languages:**
- `bash` - Shell commands
- `typescript` - TypeScript code
- `javascript` - JavaScript code
- `json` - JSON configuration
- `ini` - Systemd/config files
- `nginx` - Nginx configs
- `sql` - Database queries
- `env` - Environment files

---

## Project-Level Documentation

**Separate from Global-Docs!**

### When to Document in Project

- Business logic specific to this project
- Custom implementations for this client
- Project-specific configurations
- Temporary solutions

### Project Documentation Location

```
project-root/
├── docs/
│   ├── PROJECT-SPECIFIC-FEATURE.md
│   ├── BUSINESS-REQUIREMENTS.md
│   ├── API-DOCUMENTATION.md
│   └── DEPLOYMENT-NOTES.md
└── Global-Docs/  ← Symlink to global docs
```

### When to Move to Global

If project documentation becomes:
- Reusable across projects
- General pattern/approach
- Technology-specific solution
- Best practice implementation

→ Move to Global-Docs and reference from project

---

## Milestone-Based Documentation

### Every 45-60 Minute Milestone

**Check:**

1. Did I build something complex?
2. Did I solve a difficult problem?
3. Did I learn something important?
4. Will this be useful in future projects?

**If YES to any, document it!**

### Milestone Documentation Template

```markdown
## Milestone: [Brief Description]

**Completed:** YYYY-MM-DD HH:MM UTC
**Duration:** X minutes
**Complexity:** Low/Medium/High

### What Was Built

### Key Challenges

### Solutions Implemented

### Lessons Learned

### Reusability Assessment
- [ ] Reusable across projects
- [ ] Technology-specific solution
- [ ] Best practice pattern
- [ ] Requires documentation: YES/NO

### Documentation Status
- [ ] Created new Global-Docs file: [filename]
- [ ] Updated existing file: [filename]
- [ ] No documentation needed (project-specific)
```

---

## Maintenance Rules

### Regular Review (Monthly)

1. **Check for outdated content**
   - Technology versions changed?
   - Better approaches discovered?
   - Deprecated patterns?

2. **Consolidate similar docs**
   - Multiple files on same topic?
   - Overlapping content?
   - Opportunity to merge?

3. **Update examples**
   - Code still works?
   - Best practices current?
   - Links still valid?

### Version History

**Add to bottom of file:**

```markdown
---

## Version History

### 2025-10-19
- Initial documentation
- Added setup instructions
- Documented troubleshooting steps

### 2025-11-15
- Updated for new API version
- Added performance optimization section
- Fixed broken examples
```

---

## Cross-Project Linking

### From Global-Docs to Project

```markdown
**Example Implementation:**
See [Innovation Forge Website](E:\Vibe Code\Innovation Forge\Website\)
- `lib/ai/exa-client.ts` - Integration example
- `lib/article-generator.ts` - Usage pattern
```

### From Project to Global-Docs

```markdown
<!-- In project README or docs -->
**Email System:**
See [Global-Docs: AWS-SES-EMAIL-INTEGRATION.md](./Global-Docs/AWS-SES-EMAIL-INTEGRATION.md)
```

---

## Automation Checklist

**Before each milestone report:**

- [ ] Check for new complex components built
- [ ] Review for reusable patterns
- [ ] Search existing Global-Docs for related content
- [ ] Determine: Create new / Update existing / Merge
- [ ] Generate or update documentation
- [ ] Update "Last Updated" date
- [ ] Test all code examples
- [ ] Verify all links work
- [ ] Update related documentation cross-references

**After documentation:**

- [ ] Verify file in `C:\Users\kento\.cursor\global-cursor-repo\docs\`
- [ ] Confirm symlink works in project: `Global-Docs\YOUR-FILE.md`
- [ ] Add to related docs "See Also" sections
- [ ] Update any index or navigation files

---

## Examples from Innovation Forge Project

### Components Documented

1. **AI-COLLABORATIVE-AUTHORING-SYSTEM.md**
   - Multi-model AI system
   - MCP server integration
   - Systemd daemon
   - Database schema
   - Quality validation

2. **EXA-MCP-SERVER-SETUP.md**
   - Standalone MCP server
   - API integration
   - Configuration
   - Usage patterns

3. **PERPLEXITY-ASK-MCP-SERVER-SETUP.md**
   - Similar structure to Exa
   - Different API
   - Model selection guide

4. **SYSTEMD-DAEMON-SETUP.md**
   - Production automation
   - Timer configuration
   - Logging setup
   - Troubleshooting

5. **AWS-SES-EMAIL-INTEGRATION.md**
   - Email system setup
   - Environment variable conflicts
   - Multi-tenant solutions
   - Email template best practices

6. **MULTI-TENANT-DEPLOYMENT.md**
   - Server architecture
   - Port allocation
   - Database isolation
   - Nginx configuration

### What Was NOT Documented

- Business logic for Innovation Forge
- Specific article topics
- Client requirements
- Temporary test scripts
- Project-specific styling

---

## Path Substitution Rules

**CRITICAL:** When creating Global-Docs, use platform-agnostic paths:

### Windows Paths
Replace: `C:\Users\kento\.cursor\`
With: `%UserProfile%\.cursor\`

### Linux/Mac Paths
Replace: `/home/kento/.cursor/`
With: `$HOME/.cursor/`

### Examples

**❌ Bad:**
```bash
cd C:\Users\kento\.cursor\exa-mcp-server
```

**✅ Good:**
```bash
cd %UserProfile%\.cursor\exa-mcp-server  # Windows
cd $HOME/.cursor/exa-mcp-server          # Linux/Mac
```

**✅ Even Better (Both platforms):**
```bash
# Windows
cd %UserProfile%\.cursor\exa-mcp-server

# Linux/Mac
cd $HOME/.cursor/exa-mcp-server
```

---

## Quality Checklist

Before considering documentation complete:

- [ ] **Accurate:** All commands tested and work
- [ ] **Complete:** No missing critical steps
- [ ] **Clear:** Non-expert can follow
- [ ] **Practical:** Real examples, not theory
- [ ] **Cross-referenced:** Links to related docs
- [ ] **Troubleshooting:** Common issues covered
- [ ] **Platform-agnostic:** Uses `$HOME` or `%UserProfile%`
- [ ] **Up-to-date:** Date stamp current
- [ ] **Formatted:** Proper markdown, code blocks
- [ ] **Spell-checked:** No typos

---

## Related Rules

- [Context-Cache-Management.md](../rules/context-cache-management.md) - When to clear context
- [Milestone-Reporting.md](../workflows/milestone-reporting.md) - When to report
- [Global-Repository-Rules.md](../rules/global-repository-rules.md) - Repository structure

---

**Last Updated:** October 19, 2025  
**Rule Type:** Automatic / Milestone-Based  
**Priority:** High  
**Applies To:** All complex implementations

