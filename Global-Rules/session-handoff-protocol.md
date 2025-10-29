# Session Handoff Protocol

## Trigger Command

When user says **"create handoff"**, **"generate handoff"**, or **"session handoff"**, automatically execute this complete protocol.

---

## Handoff Document Structure

Create a comprehensive handoff document: `SESSION-HANDOFF-[DATE].md` in `.project-memory/history/`

### Required Sections

#### 1. Session Summary
- **Date & Time:** Session start and end timestamps
- **Duration:** Total session time
- **Session ID:** Unique identifier for this session
- **Primary Focus:** Main task/feature worked on
- **Status:** In Progress / Completed / Blocked

#### 2. Work Completed
- Detailed list of everything accomplished
- Files created/modified/deleted
- Features implemented
- Bugs fixed
- Database changes (migrations, schema updates)
- Configuration changes
- Dependencies added/updated

#### 3. Current State
- What's working
- What's partially implemented
- What's tested vs not tested
- Known issues or bugs
- Technical debt introduced
- Performance considerations

#### 4. Next Steps (Prioritized)
1. Immediate next action (what to do first)
2. Short-term tasks (next 2-4 hours)
3. Medium-term tasks (next session)
4. Long-term considerations
5. Optional improvements

#### 5. File Locations
- **Log Files:** Exact paths to relevant logs
- **Key Files Modified:** List with descriptions
- **New Files Created:** Purpose of each
- **Configuration Files:** Any .env or config changes
- **Database Files:** Migration files, seed data

#### 6. Testing Status
- **Unit Tests:** Pass/Fail/Not Run
- **Integration Tests:** Status
- **End-User Testing:** Completed/Pending
- **Screenshots:** Locations if frontend work
- **Playwright Results:** If UI testing performed

#### 7. Dependencies & Prerequisites
- Required environment variables
- Services that must be running (database, API, etc.)
- External dependencies installed
- System requirements

#### 8. Commands to Resume Work
```bash
# Exact commands to get started
cd /path/to/project
docker-compose up -d
npm run dev
# etc.
```

#### 9. Memory System References
- **History Entries:** Related past work to review
- **Reasoning Documents:** Business logic to understand
- **Architecture Decisions:** Relevant design choices

#### 10. Warnings & Gotchas
- Things to be careful about
- Known breaking points
- Areas needing refactoring
- Security considerations

---

## Handoff Prompt Format

Generate a **copy-able prompt box** at the end of the handoff document:

````markdown
## 📋 Handoff Prompt for Next Session

```prompt
[Project Name] - Session Handoff

**Date:** [YYYY-MM-DD HH:MM]
**Previous Session Focus:** [Brief description]

## Quick Start

1. Navigate to project: `cd [full path]`
2. Start services: [commands]
3. Review handoff: `.project-memory/history/SESSION-HANDOFF-[DATE].md`

## Current Status

[2-3 sentence summary of where things are]

## Immediate Next Steps

1. [First action - be specific]
2. [Second action]
3. [Third action]

## Critical Context

- **Log Files:** [locations]
- **Key Files:** [list]
- **What's Working:** [summary]
- **What Needs Work:** [summary]

## Development Protocol

Use the following protocols for this work:
- ✅ **Autonomous Development Protocol** (Global-Workflows/)
- ✅ **45-Minute Milestones** (Conservative estimates, regular checkpoints)
- ✅ **Peer-Based Coding** (docs/Peer-Coding.md)
- ✅ **Pairwise Testing** (Global-Workflows/Pairwise-Comprehensive-Testing.md)
[If frontend work:]
- ✅ **Playwright Testing** (Full page screenshots, UI automation)
- ✅ **End-User Testing** (docs/End-User-Testing.md)

## Memory Systems

Before starting:
1. Read: `.cursor/memory/active/CURRENT_FOCUS.md`
2. Read: `.cursor/memory/active/ACTIVE_WORK.md`
3. Review: `.project-memory/history/` (recent entries)
4. Check: `.project-memory/reasoning/` (relevant logic)

Update these as you work to maintain context for future sessions.

## Session Guidelines

- Create todos for complex tasks (3+ steps)
- Commit after each logical completion
- Update memory files as insights emerge
- Run resource cleanup after 45-minute milestones
- Document decisions in reasoning repository

## Questions to Ask

1. Should I start with [specific task]?
2. Are there any changes to priorities?
3. Do you want me to proceed autonomously or check in?

Ready to continue work on [Project Name]. Please confirm or adjust priorities.
```
````

**Note:** The above prompt box will have a Copy button in Cursor's UI (upper right corner) for easy copying.

---

## Frontend-Specific Additions

If frontend work was performed, add:

### Frontend Testing Checklist

- [ ] Full page screenshots captured (organized by route/feature)
- [ ] Playwright tests written and passing
- [ ] Mobile responsive testing completed
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Accessibility testing (keyboard navigation, screen readers)
- [ ] Performance testing (Lighthouse scores)
- [ ] Visual regression testing
- [ ] Form validation testing
- [ ] Error state handling verified
- [ ] Loading states verified
- [ ] Empty states verified

### Screenshot Organization

```
.playwright/screenshots/
├── homepage/
│   ├── desktop-1920x1080.png
│   ├── tablet-768x1024.png
│   └── mobile-375x667.png
├── [feature-name]/
│   └── ...
```

### Playwright Test Locations

- **Test Files:** `tests/` or `e2e/`
- **Configuration:** `playwright.config.ts`
- **Results:** `.playwright/test-results/`
- **Video Recordings:** `.playwright/videos/` (if enabled)

### UI Testing Notes

Document any:
- Flaky tests that need attention
- Components needing visual regression tests
- Areas not covered by automation
- Manual testing performed
- Browser-specific issues found

---

## Autonomous Protocol Integration

Include clear instructions to use:

### Development Protocols

```markdown
## 🤖 Autonomous Development

This work should proceed using:

1. **Autonomous Development Protocol**
   - Location: `Global-Workflows/Autonomous-Development-Protocol.md`
   - Proceed without asking for approval on standard operations
   - Make decisions based on best practices and project patterns

2. **45-Minute Milestones**
   - Break work into 45-minute conservative estimates
   - Report progress at each milestone
   - Run `scripts/resource-cleanup.sh` after each milestone
   - Capture timestamp at start: `date -u +"%Y-%m-%d %H:%M:%S UTC"`

3. **Peer-Based Coding**
   - Location: `docs/Peer-Coding.md`
   - Primary model writes initial implementation
   - Different top AI model conducts peer review
   - Apply fixes categorized by severity (Critical/High/Medium/Low)
   - Log reviews to `.logs/peer-review/`

4. **Pairwise Testing**
   - Location: `Global-Workflows/Pairwise-Comprehensive-Testing.md`
   - Tester AI develops and tests code
   - Reviewer AI independently validates
   - Iterates until ZERO issues
   - Mandatory for frontend changes

[If frontend:]
5. **End-User Testing**
   - Location: `docs/End-User-Testing.md`
   - Use Playwright to test as end user would
   - Screenshot EVERY page, verify, then delete
   - Test ALL forms, links, flows
   - Check emails in MailHog
   - Verify database updates
```

---

## Memory System Integration

### Before Ending Session

1. **Update Active Work**
   ```bash
   # Update .cursor/memory/active/ACTIVE_WORK.md
   - Add completed tasks to "Completed Recently"
   - Update "Next Steps" with prioritized actions
   - Document any "Recent Decisions"
   ```

2. **Update Current Focus**
   ```bash
   # Update .cursor/memory/active/CURRENT_FOCUS.md
   - Describe current state
   - What's working vs what needs work
   - Context for next session
   ```

3. **Create History Entry**
   ```bash
   # Create .project-memory/history/SESSION-HANDOFF-[DATE].md
   - Full handoff document (as described above)
   - Preserves all work details
   - Committed to Git for sharing
   ```

4. **Update Reasoning (if applicable)**
   ```bash
   # If new business logic or design decisions emerged:
   # Create/update .project-memory/reasoning/[topic].md
   - Document why things work the way they do
   - Capture business rules
   - Explain restrictions or design rationale
   ```

### For Next Session

Include these instructions in handoff prompt:

```markdown
## Memory System Usage

1. **Read Session Memory** (`.cursor/memory/`)
   - PROJECT_BRIEF.md - Project overview
   - TECH_STACK.md - Technologies used
   - ARCHITECTURE.md - Design decisions
   - PATTERNS.md - Coding conventions
   - active/CURRENT_FOCUS.md - Where we are
   - active/ACTIVE_WORK.md - What's next

2. **Review Project History** (`.project-memory/history/`)
   - Recent SESSION-HANDOFF-*.md files
   - Related feature implementation docs
   - Past milestone completion reports

3. **Check Reasoning** (`.project-memory/reasoning/`)
   - Business logic related to current task
   - Design rationale for components you'll modify
   - Restrictions or rules that apply

4. **Update As You Work**
   - Keep CURRENT_FOCUS.md updated
   - Add completed items to ACTIVE_WORK.md
   - Create new reasoning docs for new patterns
   - Log milestones to history
```

---

## Log File Management

### Standard Log Locations

Document all relevant logs:

```markdown
## 📁 Log Files

### Session Logs
- `.cursor/ai-logs/[timestamp]-*.log` - AI session logs

### Application Logs
- `logs/app.log` - Application runtime logs
- `logs/error.log` - Error logs
- `logs/access.log` - Access logs

### Testing Logs
- `.playwright/test-results/` - Playwright test outputs
- `.logs/peer-review/` - Peer review results
- `coverage/` - Test coverage reports

### Build Logs
- `.next/` - Next.js build cache
- `node_modules/.cache/` - Build tool caches

### Database Logs
- `docker-compose logs postgres` - PostgreSQL logs
- `migrations/` - Migration history

### Development Server Logs
- Check terminal output or background process logs
- For background: `jobs` or `ps aux | grep node`
```

---

## Implementation Checklist

When creating handoff, ensure:

- [ ] SESSION-HANDOFF-[DATE].md created in `.project-memory/history/`
- [ ] All 10 required sections completed
- [ ] Copy-able prompt box included
- [ ] Frontend testing section (if applicable)
- [ ] Autonomous protocol instructions clear
- [ ] Memory system guidance included
- [ ] Log file locations documented
- [ ] Next steps prioritized and specific
- [ ] Commands to resume work provided
- [ ] File committed to Git
- [ ] Active work files updated
- [ ] Current focus updated

---

## Example Handoff Prompt Output

The final handoff should include a properly formatted prompt box like this:

```
## 📋 Copy This Prompt to Resume Work

[Full prompt text here - formatted for easy copy/paste]
```

This box will automatically get a Copy button in Cursor's markdown preview.

---

## Git Commit

After creating handoff:

```bash
git add .project-memory/history/SESSION-HANDOFF-[DATE].md
git add .cursor/memory/active/*.md
# Use wrapper script that auto-pushes to GitHub
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-commit-and-push.ps1" -Message "chore(cursor): session handoff for [date] - [brief description] [chat:session-handoff]"

# Or manually:
# git commit -m "chore(cursor): session handoff for [date] - [brief description] [chat:session-handoff]

Completed:
- [List major accomplishments]

Next Steps:
- [First priority]
- [Second priority]

See .project-memory/history/SESSION-HANDOFF-[DATE].md for full details"
```

---

## Automation

This entire protocol activates automatically when user says:
- "create handoff"
- "generate handoff"  
- "session handoff"
- "handoff document"
- "prepare handoff"

AI should:
1. Generate complete handoff document
2. Update all memory files
3. Create copy-able prompt box
4. Commit to Git
5. Confirm completion with summary

---

## Version History

- **v1.0** - 2025-10-18 - Initial session handoff protocol
- Created to streamline session transitions
- Integrates all development protocols
- Ensures memory system utilization
- Provides copy-able prompts for Cursor

---

**Use this protocol to create seamless handoffs between AI sessions, ensuring no context or progress is lost.**

