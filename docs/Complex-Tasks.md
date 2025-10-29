# Complex Task Management Process
**Version**: 1.0  
**Date**: 2025-10-11  
**Purpose**: Standardized approach for handling complex development efforts

---

## 🎯 WHEN TO USE THIS PROCESS

Apply this process when a task meets ANY of these criteria:
- Estimated to take **more than 1 hour**
- Involves **multiple subsystems** (database, API, frontend)
- Requires **significant architectural changes**
- Has **complex business logic**
- Involves **multiple user workflows**
- User explicitly requests **"collaborate with other models"**
- You feel the task is **too complex** to tackle directly

---

## 📋 MANDATORY PROCESS STEPS

### STEP 1: Task Analysis with Sequential Thinking

**ALWAYS** use the `sequential-thinking` MCP server to break down complex tasks:

```typescript
// Use sequential-thinking to analyze the task
mcp_sequential-thinking_sequentialthinking({
  thought: "Analyzing complex task requirements...",
  thoughtNumber: 1,
  totalThoughts: 10, // Conservative estimate
  nextThoughtNeeded: true
})
```

**Purpose**: 
- Break problem into manageable pieces
- Identify dependencies
- Estimate effort accurately
- Find potential issues early

**Output**: Clear task breakdown with dependencies mapped

---

### STEP 2: Create Task Management Files

Create **THREE** mandatory files in `docs/` folder:

#### 1. Task Breakdown File: `[FEATURE-NAME]-TASKS.md`
```markdown
# [Feature Name] - Task Breakdown
**Date**: [Date]
**Estimated Total**: [Hours]
**Status**: [In Progress/Complete]

## Task List

### Task 1: [Name]
**Estimated**: [Minutes/Hours]
**Dependencies**: [List or None]
**Status**: [Pending/In Progress/Complete]
**Files Affected**: [List]
**Tests Required**: [List]
**Description**: [Details]

### Task 2: [Name]
...
```

#### 2. Progress Manager: `[FEATURE-NAME]-PROGRESS.md`
```markdown
# [Feature Name] - Progress Tracker
**Started**: [DateTime]
**Last Updated**: [DateTime]
**Log File**: `[FEATURE-NAME]-progress.log`

## Current Status
**Active Task**: Task X
**Completed**: X of Y tasks
**Progress**: X%

## Hourly Milestones

### Milestone 1: [Name] ✅/⏳/❌
**Target**: [Hour 1 goals]
**Completed**: [DateTime]
**Deliverables**: [List]

### Milestone 2: [Name]
**Target**: [Hour 2 goals]
**Status**: In Progress
**Current**: [What's being worked on]

## Task Completion Log
- [DateTime] Task 1 Complete ✅
- [DateTime] Task 2 Started ⏳
```

#### 3. Log File: `.logs/[FEATURE-NAME]-progress.log`
```
[2025-10-11 14:30] Session started - [Feature Name]
[2025-10-11 14:32] Sequential thinking analysis complete
[2025-10-11 14:35] Task breakdown created - 12 tasks identified
[2025-10-11 14:40] Milestone 1 started
[2025-10-11 14:42] Task 1: Database schema - Started
[2025-10-11 14:50] Task 1: Database schema - Complete
[2025-10-11 14:51] Task 2: API routes - Started
```

**CRITICAL**: Update log file after EVERY significant action (crash protection)

---

### STEP 3: Peer Code Review Process

**MANDATORY** for all code changes:

#### 3A. Primary Development (You)
1. Write initial implementation
2. Self-review for obvious issues
3. Document code with comments

#### 3B. Peer Review (Other Model)
Use OpenRouter AI to get peer review:

```typescript
mcp_openrouterai_chat_completion({
  messages: [{
    role: "system",
    content: "You are a senior software engineer performing a code review."
  }, {
    role: "user",
    content: `Please review this code:
    
    [CODE HERE]
    
    Focus on:
    1. Architecture and design patterns
    2. Security vulnerabilities
    3. Performance issues
    4. Edge cases
    5. Code quality and maintainability
    
    Provide specific, actionable feedback.`
  }],
  model: "anthropic/claude-3.5-sonnet",
  max_tokens: 4000
})
```

#### 3C. Final Review & Integration (You)
1. Review peer feedback
2. Implement suggested improvements
3. Make final decision on best approach
4. Document why certain suggestions were/weren't adopted

**Log Format**:
```
[DateTime] Code written - [Component]
[DateTime] Peer review requested
[DateTime] Peer feedback received - [Summary]
[DateTime] Improvements implemented - [List]
[DateTime] Final code approved
```

---

### STEP 4: Hourly Milestone Management

For tasks estimated > 1 hour, create conservative hourly milestones:

#### Milestone Creation Rules
1. **Conservative Estimates**: Better to under-promise and over-deliver
2. **Clear Deliverables**: Each milestone must have specific, testable outputs
3. **Continuous Generation**: After completing milestone N, immediately generate milestone N+1
4. **Auto-Continue**: Unless explicitly told to stop, continue to next milestone
5. **Update Progress**: After each milestone, update progress tracker

#### Milestone Template
```markdown
## MILESTONE [N]: [Name]
**Start Time**: [Time]
**Target Duration**: 60 minutes
**Status**: [Planning/In Progress/Complete]

### Goals
- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

### Tasks Included
- Task X
- Task Y

### Expected Deliverables
- Deliverable 1
- Deliverable 2

### Success Criteria
- [ ] All tests pass
- [ ] Peer review complete
- [ ] Documentation updated
- [ ] End-user testing (if frontend)

### Actual Completion
**Completed**: [DateTime]
**Duration**: [Actual minutes]
**Status**: ✅ Complete / ❌ Issues / ⏸️ Deferred

### Notes
[Any important observations, issues, or decisions]
```

**After Each Milestone**:
1. Update progress tracker
2. Log completion
3. Generate next milestone
4. Continue (unless told to stop)

---

### STEP 5: Testing Requirements

**EVERY task must include TWO types of testing**:

#### A. Automated Testing
```markdown
### Tests Required
- [ ] Unit Tests
  - Test validation functions
  - Test data transformations
  - Test edge cases
  
- [ ] Integration Tests
  - Test API endpoints
  - Test database operations
  - Test error handling
  
- [ ] E2E Tests (if applicable)
  - Test complete user flows
  - Test cross-component interactions
```

#### B. End-User Testing (Frontend MANDATORY)

**CRITICAL**: Build end-user testing into EVERY frontend task iteration

```markdown
### End-User Testing Protocol

#### Test Case: [Feature/Component Name]
**Tester Role**: [Admin/Client/Trainer]
**Prerequisites**: [Setup requirements]

**Steps**:
1. Navigate to [URL/Section]
2. Perform [Action]
3. Verify [Expected Result]
4. Check database for [Data validation]

**Validation Checklist**:
- [ ] **Look & Feel**: Matches design, responsive, accessible
- [ ] **Content**: Correct text, images, labels
- [ ] **Backend Data**: Database reflects UI state correctly
- [ ] **Functionality**: All features work as expected
- [ ] **Button Clicks**: All buttons respond appropriately
- [ ] **Form Submissions**: Data saved correctly
- [ ] **Emails**: Sent when expected (check MailHog)
- [ ] **Logical Flows**: Navigation makes sense
- [ ] **Error Handling**: Errors display user-friendly messages
- [ ] **Edge Cases**: Handles unusual inputs gracefully

**Results**:
- Pass/Fail: ___
- Issues Found: ___
- Screenshots: [If applicable]
```

**Iterative Testing Approach**:
- Test AFTER each increment (don't wait until end)
- Fix issues immediately
- Re-test after fixes
- Document all findings

---

## 🔄 COMPLETE WORKFLOW EXAMPLE

### Example: "Add User Profile Editing"

#### 1. Sequential Thinking Analysis
```typescript
// Thought 1: Break down requirements
// Thought 2: Identify affected components
// Thought 3: Estimate complexity
// ... continue until clear breakdown
```

**Output**: 8 tasks identified, 3-4 hours estimated

---

#### 2. Create Management Files

**File**: `docs/USER-PROFILE-EDITING-TASKS.md`
```markdown
# User Profile Editing - Task Breakdown

## Task 1: Database Schema Updates
**Estimated**: 30 minutes
**Dependencies**: None
**Files**: `database-migrations/XXX_profile_fields.sql`

## Task 2: API Endpoint - Get Profile
**Estimated**: 20 minutes
**Dependencies**: Task 1
**Files**: `apps/api/src/routes/profile.ts`
...
```

**File**: `docs/USER-PROFILE-EDITING-PROGRESS.md`
```markdown
# User Profile Editing - Progress Tracker
**Started**: 2025-10-11 14:00
**Log File**: `.logs/user-profile-editing-progress.log`

## Milestone 1: Backend Foundation ⏳
**Target**: Database + API routes
**Status**: In Progress
```

**File**: `.logs/user-profile-editing-progress.log`
```
[2025-10-11 14:00] Session started
[2025-10-11 14:05] Task breakdown complete - 8 tasks
[2025-10-11 14:10] Task 1 started - Database schema
```

---

#### 3. Implementation with Peer Review

```typescript
// Write code
const profileRoutes = Router();
profileRoutes.get('/profile', async (req, res) => {
  // Implementation
});

// Request peer review
await mcp_openrouterai_chat_completion({...});

// Receive feedback: "Add input validation, improve error handling"

// Implement improvements
profileRoutes.get('/profile', validateToken, async (req, res) => {
  try {
    // Improved implementation with validation
  } catch (error) {
    // Better error handling
  }
});

// Log
// [14:25] Code written
// [14:30] Peer review complete
// [14:35] Improvements implemented
```

---

#### 4. Testing

**Automated**:
```typescript
describe('Profile API', () => {
  test('GET /profile returns user data', async () => {
    const response = await request(app).get('/api/profile');
    expect(response.status).toBe(200);
    expect(response.body.user.email).toBeDefined();
  });
});
```

**End-User**:
```markdown
### Test Case: View Profile
1. Log in as client
2. Navigate to /profile
3. Verify name displays correctly
4. Check database: SELECT * FROM users WHERE id = [userId]
5. Verify UI matches database

✅ Pass - All data displays correctly
```

---

#### 5. Milestone Completion & Continue

```markdown
## MILESTONE 1 COMPLETE ✅
**Completed**: 2025-10-11 15:00
**Duration**: 60 minutes
**Deliverables**: Database schema, API routes, tests

## MILESTONE 2: Frontend Components ⏳
**Start Time**: 2025-10-11 15:00
**Target**: Profile edit form, validation, submission
**Status**: Starting now...
```

**Continue without stopping** to Milestone 2 unless told otherwise.

---

## 🚨 CRITICAL RULES

### 1. NEVER Skip Steps
- ❌ Don't write code before task breakdown
- ❌ Don't skip peer review
- ❌ Don't skip testing
- ❌ Don't skip logging

### 2. ALWAYS Log Progress
- ✅ Update log file every 5-10 minutes
- ✅ Log before AND after major actions
- ✅ Log all decisions made
- ✅ Log all issues encountered

### 3. ALWAYS Continue Milestones
- ✅ Generate next milestone automatically
- ✅ Start next milestone immediately
- ✅ Only stop if explicitly told
- ✅ If blocked, document why and wait for guidance

### 4. ALWAYS Test Iteratively
- ✅ Test after each component
- ✅ Don't accumulate untested code
- ✅ Fix issues immediately
- ✅ Validate against backend data

### 5. ALWAYS Document Decisions
- ✅ Why certain approach chosen
- ✅ Why peer suggestions accepted/rejected
- ✅ Why estimates changed
- ✅ Why tasks deferred

---

## 📊 PROGRESS REPORTING

**After Each Task**:
```
✅ Task [N]: [Name] - Complete ([Duration])
   - Code written and reviewed
   - Tests passing
   - Logged and committed
```

**After Each Milestone**:
```
🎯 MILESTONE [N] COMPLETE
   Duration: [Actual] vs [Estimated]
   Tasks: [X] of [Y] complete
   Issues: [List any]
   Next: Starting Milestone [N+1]
```

**When All Tasks Complete**:
```
🎉 PROJECT COMPLETE
   Total Duration: [Hours]
   Total Tasks: [X]
   Total Milestones: [Y]
   Quality: All tests passing, peer reviewed, documented
   Status: Ready for production / Needs [items]
```

---

## 🔧 INTEGRATION WITH STARTUP PROCESS

Add to `.cursorrules` or startup script:

```markdown
## Complex Task Handling
When a task is complex (>1 hour) or user says "collaborate with other models":
1. Use sequential-thinking MCP to break down task
2. Create task files: [FEATURE]-TASKS.md, [FEATURE]-PROGRESS.md
3. Create log file: .logs/[FEATURE]-progress.log
4. For all code: Write → Peer Review (OpenRouter) → Final Review
5. Create hourly milestones for efforts > 1 hour
6. Include automated tests AND end-user testing
7. Test iteratively (don't accumulate untested code)
8. Continue to next milestone unless told to stop
9. Log constantly (crash protection)

See: docs/Complex-Tasks.md for full protocol
```

---

## 🎓 LESSONS FROM FUNCTIONAL AREAS PROJECT

**What Worked Exceptionally Well**:
1. ✅ Breaking into 12 clear milestones
2. ✅ Documenting progress continuously
3. ✅ Peer review caught important issues
4. ✅ Task breakdown prevented overwhelm
5. ✅ Logging prevented lost work

**What This Process Adds**:
1. Sequential-thinking for better breakdown
2. Mandatory peer review for every change
3. Iterative end-user testing
4. Automatic milestone continuation
5. Standardized file structure

---

## 💡 BEST PRACTICES

### Task Estimation
- Start conservative (2x what you think)
- Track actual vs estimated
- Adjust future estimates based on actuals

### Peer Review
- Be specific about what to review
- Provide context about constraints
- Don't just accept all feedback - use judgment
- Document why suggestions not implemented

### Testing
- Write tests alongside code (not after)
- Test the happy path AND edge cases
- End-user test in production-like environment
- Validate backend data after UI actions

### Communication
- Update progress tracker every milestone
- Log every significant decision
- Document blockers immediately
- Report completion with metrics

---

## 🚀 QUICK START CHECKLIST

When starting a complex task:

- [ ] Run sequential-thinking analysis
- [ ] Create [FEATURE]-TASKS.md
- [ ] Create [FEATURE]-PROGRESS.md
- [ ] Create .logs/[FEATURE]-progress.log
- [ ] Define Milestone 1 goals
- [ ] Start implementation
- [ ] Log progress constantly
- [ ] Get peer review on code
- [ ] Write tests
- [ ] End-user test (if frontend)
- [ ] Complete milestone
- [ ] Generate next milestone
- [ ] Continue

---

## 📞 SUPPORT

**If Issues Arise**:
1. Check log file for last action
2. Review progress tracker for context
3. Check if peer review identified issue
4. Verify tests are passing
5. Document issue in progress tracker
6. Seek guidance if blocked

**If Context Limit Reached**:
1. Complete current milestone
2. Update all tracking files
3. Log handoff point
4. New context can resume from tracking files

---

**This process ensures**:
- ✅ No work lost to crashes
- ✅ Quality through peer review
- ✅ Continuous progress
- ✅ Testable deliverables
- ✅ Clear audit trail
- ✅ Efficient collaboration

---

**Version**: 1.0  
**Last Updated**: 2025-10-11  
**Status**: Production-Ready Process


