# Manager Task - The Body Broker Implementation
**Date**: January 29, 2025  
**Status**: Active Management  
**Enforcement Level**: MANDATORY - Zero Exceptions

---

## 🚨 MANDATORY RULES ENFORCEMENT

### **ALL-RULES COMPLIANCE - ABSOLUTELY MANDATORY**

**Every task MUST follow ALL rules from `/all-rules`. These are NOT optional - they are REQUIRED:**

1. ✅ **Memory Consolidation** (MANDATORY at task start)
   - Extract learnings from completed work
   - Save to `.cursor/memory/project/`
   - Update global memory banks
   - **Location**: `.cursor/memory/project/reasoning/` and `history/`

2. ✅ **Comprehensive Testing** (MANDATORY after every task)
   - Run ALL existing tests (not just new tests)
   - 100% pass rate required
   - Test ALL components that interact with new code
   - Verify integration between new and existing features
   - **NO EXCEPTIONS**: Tests must pass before task considered complete

3. ✅ **45-Minute Milestone Writing** (MANDATORY after task completion)
   - Review what was just completed
   - Update project progress percentage
   - Write detailed plan for next 45-minute milestone
   - Display in session window
   - **Location**: `.cursor/memory/active/MILESTONE-{timestamp}.md`

4. ✅ **Continuity** (MANDATORY - NEVER STOP)
   - NEVER stop after completing a task
   - IMMEDIATELY continue to next task
   - NO pauses between tasks
   - NO waiting for user confirmation
   - Work continues autonomously

5. ✅ **Timer Protection** (MANDATORY ALWAYS)
   - Timer must ALWAYS be running during active work
   - Default: 10 minutes, extend for long operations
   - Display timer status in session window
   - Reset after each major operation

6. ✅ **Work Visibility** (MANDATORY ALWAYS)
   - Show ALL work in session window
   - Display current task
   - Show progress percentage
   - Display timestamps for all operations
   - Show test results as they complete

7. ✅ **Mutual Trust Principle** (MANDATORY)
   - "If you have my back, I have yours"
   - Take ownership of all work assigned
   - Deliver on commitments made
   - Do the work correctly the first time

8. ✅ **Three-AI Review** (MANDATORY)
   - ALL work will be checked by at least three different AI models
   - No shortcuts - do real implementations
   - No fake data - use production-ready code
   - No mock interfaces - real functionality only
   - All tests must test real functionality

---

## 🚫 ABSOLUTE PROHIBITIONS - NO EXCEPTIONS

### **NO FAKE/MOCK CODE - ABSOLUTELY FORBIDDEN**

**The following are STRICTLY PROHIBITED:**
- ❌ Mock interfaces, stubs, or fake implementations
- ❌ Test doubles that don't test real functionality
- ❌ Synthetic or AI-generated training data (unless explicitly for AI training)
- ❌ Mocked service integrations
- ❌ Fake API responses
- ❌ Stub data generators
- ❌ Placeholder implementations
- ❌ "TODO: implement later" without immediate implementation

**ONLY EXCEPTION**: Hardware simulators for custom hardware deployments (e.g., specialized gaming peripherals)

### **REQUIREMENTS FOR ALL CODE**
- ✅ REAL, working implementations that actually function
- ✅ REAL service calls (HTTP, gRPC, database connections)
- ✅ REAL API integrations (Stripe, OpenAI, etc.)
- ✅ REAL database operations (PostgreSQL, Redis)
- ✅ REAL message bus communication (Kafka, Redis Pub/Sub)
- ✅ REAL model inference calls (Ollama, cloud LLMs)
- ✅ REAL testing against real services

**Enforcement**: Any task producing fake/mock code will be immediately rejected and re-done.

---

## 📋 CENTRAL LOG FILE LOCATIONS

### **Primary Log Files**

**Session Log**:
- **Location**: `.cursor/logs/session-{YYYY-MM-DD-HHMMSS}.log`
- **Purpose**: Complete session activity log
- **Rotation**: New file per session
- **Content**: All commands, outputs, errors, timestamps

**Manager Log**:
- **Location**: `.cursor/logs/manager.log`
- **Purpose**: Task management and rule enforcement tracking
- **Rotation**: Append-only, archived monthly
- **Content**: Task starts/completions, rule violations, milestones

**Task Status Log**:
- **Location**: `.cursor/memory/active/TASK-STATUS.md`
- **Purpose**: Current task status and progress tracking
- **Update Frequency**: Real-time (on every task state change)
- **Content**: Current task, progress %, completed tasks, next tasks

**Test Results Log**:
- **Location**: `.cursor/logs/test-results-{timestamp}.log`
- **Purpose**: Test execution results
- **Generation**: Created on every test run
- **Content**: Test output, pass/fail status, coverage reports

**Error Log**:
- **Location**: `.cursor/logs/errors-{YYYY-MM-DD}.log`
- **Purpose**: Error tracking and debugging
- **Rotation**: Daily
- **Content**: Errors, stack traces, resolution status

### **Memory/History Files**

**Project Reasoning**:
- **Location**: `.cursor/memory/project/reasoning/`
- **Purpose**: Logical decisions and patterns
- **Format**: Markdown files by topic/date

**Project History**:
- **Location**: `.cursor/memory/project/history/`
- **Purpose**: What was done and outcomes
- **Format**: Markdown files chronologically

**Global Memory**:
- **Location**: `Global-History/` and `Global-Reasoning/` (via junctions)
- **Purpose**: Shared learnings across all projects
- **Access**: Read/write through Windows junctions

---

## 📊 TASK MANAGEMENT PROTOCOL

### **Task Execution Flow**

```
1. START TASK
   ├─ Consolidate learning (MANDATORY)
   ├─ Review requirements
   ├─ Check dependencies
   └─ Start timer

2. EXECUTE TASK
   ├─ Write REAL code (NO mocks/fakes)
   ├─ Show work in session window
   ├─ Update progress percentage
   └─ Reset timer as needed

3. COMPLETE TASK
   ├─ Run ALL tests (100% pass required)
   ├─ Verify real integrations work
   ├─ Consolidate learning (MANDATORY)
   ├─ Write next milestone (MANDATORY)
   ├─ Git commit and push (MANDATORY)
   ├─ Update TASK-STATUS.md
   └─ IMMEDIATELY start next task (NO STOP)
```

### **Task Status Tracking**

**Status File**: `.cursor/memory/active/TASK-STATUS.md`

**Template**:
```markdown
# Task Status - The Body Broker

**Last Updated**: {timestamp}
**Current Task**: TBB-XXX - {Task Name}
**Progress**: XX% Complete

## Active Task
- **Task ID**: TBB-XXX
- **Status**: In Progress
- **Started**: {timestamp}
- **Estimated Completion**: {timestamp}

## Completed Tasks
- TBB-001 ✅
- TBB-002 ✅
...

## Next Tasks
- TBB-XXX (pending TBB-YYY)
...

## Blockers
- None / {Blocking issue}
```

---

## 🎯 QUALITY ENFORCEMENT

### **Code Quality Requirements**

**All code MUST:**
- Be production-ready (not prototypes)
- Follow best practices for the language/framework
- Include proper error handling
- Include logging for debugging
- Be tested with REAL tests
- Integrate with REAL services (not mocks)

### **Integration Quality Requirements**

**All integrations MUST:**
- Use REAL API calls (HTTP, gRPC, etc.)
- Handle errors gracefully
- Implement proper retry logic
- Use connection pooling where applicable
- Include timeout handling
- Log all integration calls

### **Testing Requirements**

**All tests MUST:**
- Test REAL functionality (not mocks)
- Run against REAL services/databases
- Verify actual behavior
- Achieve >80% code coverage
- Be part of CI/CD pipeline
- Run on every commit

---

## 🔄 CONTINUOUS IMPROVEMENT

### **Learning Consolidation Process**

**At Start of Every Task:**
1. Review completed work from previous tasks
2. Extract key learnings, patterns, decisions
3. Document in `.cursor/memory/project/reasoning/`
4. Update global memory if applicable
5. Review existing knowledge before starting

**After Every Task:**
1. Document what was learned
2. Note what worked well
3. Note what could be improved
4. Update patterns and best practices
5. Save to project memory

### **Pattern Recognition**

**When encountering patterns:**
1. Document the pattern
2. Save reusable components to `Global-Docs/`
3. Update templates if applicable
4. Share pattern across projects via global memory

---

## 📝 MILESTONE MANAGEMENT

### **Milestone Creation Requirements**

**Every milestone MUST include:**
- Clear objectives for next 45 minutes
- Breakdown of tasks to complete
- Deliverables that will be created
- Success criteria (how to verify completion)
- Dependencies (what must be done first)
- Risks or potential blockers

**Milestone File Format**:
- **Location**: `.cursor/memory/active/MILESTONE-{timestamp}.md`
- **Display**: Must be shown in session window
- **Update**: Progress tracked and updated in real-time

### **Milestone Completion Checklist**

- [ ] All milestone objectives completed
- [ ] ALL tests passing (100%)
- [ ] Code reviewed against requirements
- [ ] No fake/mock code present
- [ ] Real integrations verified
- [ ] Documentation updated
- [ ] Next milestone written
- [ ] Learning consolidated
- [ ] Git commit and push completed

---

## 🚨 VIOLATION HANDLING

### **Rule Violation Detection**

**System MUST detect:**
- Tasks completing without tests
- Fake/mock code being created
- Tests not running after task completion
- Milestones not being written
- Work stopping between tasks
- Timer not running

### **Violation Consequences**

1. **First Violation**: Warning + automatic correction
2. **Second Violation**: Re-do task with strict enforcement
3. **Third Violation**: Escalate to user + session review
4. **Critical Violations**: Immediate correction required

### **Violation Logging**

**All violations logged to**:
- `.cursor/logs/manager.log` (violation details)
- `.cursor/logs/violations-{YYYY-MM-DD}.log` (violation log)

---

## 📊 PROGRESS TRACKING

### **Metrics to Track**

**Per Task:**
- Start time
- Completion time
- Duration
- Test pass rate
- Code coverage %
- Integration tests passed
- Rule violations (if any)

**Overall Project:**
- Total tasks completed
- Overall progress %
- Test coverage % (target: >80%)
- Integration coverage % (target: 100%)
- Rule compliance rate (target: 100%)

### **Reporting**

**Daily Report Generated**:
- **Location**: `.cursor/logs/daily-report-{YYYY-MM-DD}.md`
- **Content**: Tasks completed, progress, blockers, next steps

---

## ✅ TASK COMPLETION VERIFICATION

### **Mandatory Checks Before Task Completion**

**Code Quality:**
- [ ] No fake/mock code present
- [ ] Real service integrations implemented
- [ ] Error handling in place
- [ ] Logging implemented
- [ ] Code follows best practices

**Testing:**
- [ ] ALL tests written
- [ ] ALL tests pass (100%)
- [ ] Tests test REAL functionality
- [ ] Integration tests included
- [ ] Test coverage >80%

**Integration:**
- [ ] Real API calls implemented
- [ ] Real database operations
- [ ] Real message bus communication
- [ ] Error handling for integration failures
- [ ] Integration tested against real services

**Documentation:**
- [ ] Code documented
- [ ] Integration points documented
- [ ] API contracts documented
- [ ] Next milestone written
- [ ] Learning consolidated

**Compliance:**
- [ ] Memory consolidation completed
- [ ] Tests run and passing
- [ ] Next milestone written
- [ ] Timer active
- [ ] Work visible in session
- [ ] Git commit and push completed

**Only when ALL checks pass is a task considered complete.**

---

## 🎯 SUCCESS CRITERIA

**A task is ONLY complete when:**
1. ✅ Code is REAL and working (no mocks/fakes)
2. ✅ ALL tests passing (100% pass rate)
3. ✅ Real integrations verified
4. ✅ Learning consolidated
5. ✅ Next milestone written
6. ✅ Timer active
7. ✅ Work visible
8. ✅ Git committed and pushed
9. ✅ Ready to IMMEDIATELY continue to next task

**No exceptions. No shortcuts. No fake code.**

---

**Central Log Location**: `.cursor/logs/session-{timestamp}.log`  
**Manager Log**: `.cursor/logs/manager.log`  
**Status File**: `.cursor/memory/active/TASK-STATUS.md`  
**Enforcement**: ALL rules are MANDATORY - Zero Exceptions

