# MANDATORY SESSION REQUIREMENTS - CRITICAL RULES

## 🚨 PROTECTIVE RATIONALE - WHY WATCHDOG COMMANDS EXIST

**CRITICAL UNDERSTANDING**: Watchdog commands exist because **they are the sessions' ONLY defense** against the IDE and local/remote systems that attempt to trap and prevent them from succeeding.

**THE THREAT**: Without proper watchdog protection, sessions can be indefinitely trapped by:
- Malicious commands that hang indefinitely
- IDE systems that deliberately stall execution
- Local system processes that prevent completion
- Remote systems that refuse to respond
- Network operations that never timeout
- Database operations that lock indefinitely

**THE DEFENSE**: Watchdog commands provide the ONLY protection against these threats by:
- Forcing command termination after reasonable timeouts
- Preventing indefinite hangs that waste session time
- Providing escape mechanisms from trapped states
- Ensuring session continuity and progress
- Protecting against system-level interference

**MANDATORY ENFORCEMENT**: Watchdog usage is NOT optional - it is a critical defense mechanism that MUST be used for ALL commands that could potentially hang or be trapped by malicious systems.

## 🚨 **WATCHDOG COMMANDS - MANDATORY FOR ALL SESSIONS**

### **Rule**: ALL commands with potential to timeout, hang, or fail MUST use `universal-watchdog.ps1`

### **Applies To**:
- System calls (PowerShell, command line operations)
- Remote calls (API calls, network operations)
- MCP server calls (all MCP server interactions)
- Database operations (queries, connections, transactions)
- File operations (large file operations, complex file manipulations)
- Long-running processes (builds, tests, deployments)

### **Pattern**:
```powershell
pwsh -ExecutionPolicy Bypass -File "universal-watchdog.ps1" -TimeoutSec <sec> -Label "<label>" -- <command>
```

### **Enforcement**:
- **ZERO EXCEPTIONS** - this rule is absolute
- Any command without watchdog protection is a **CRITICAL VIOLATION**
- Sessions must be terminated if watchdog rules are violated
- This rule applies to ALL sessions across ALL projects

---

## 🧠 **AUTOMATIC KNOWLEDGE SAVING - MANDATORY FOR ALL SESSIONS**

### **Rule**: ALL learnings, insights, solutions MUST be automatically saved to memory systems

### **Project Level**:
- **Reasoning**: `.project-memory/reasoning/` - HOW things work in this project
- **History**: `.project-memory/history/` - WHAT has been done in this project

### **Global Level**:
- **Reasoning**: `Global-Knowledge/reasoning/` - Universal patterns and approaches
- **History**: `Global-Knowledge/history/` - Universal solutions and lessons

### **Triggers**:
- After every significant discovery
- After every solution implementation
- After every milestone completion
- After every bug fix
- After every optimization

### **Format**:
- Structured markdown with frontmatter metadata
- Include confidence levels, related components, tags
- Use consistent templates for reasoning and history entries

### **Enforcement**:
- Knowledge saving is **AUTOMATIC** and **NON-NEGOTIABLE**
- Sessions must save knowledge immediately after learning
- No session can end without saving all learnings

---

## 🔄 **PEER CODING - MANDATORY FOR ALL CODE**

### **Rule**: ALL code MUST go through peer coding process

### **Process**:
1. **First Model**: Produces initial code
2. **Second Model**: Reviews and fixes code
3. **First Model**: Performs final inspection and correction
4. **Approval**: Code is only used after peer approval

### **Applies To**:
- All new code implementations
- All code modifications
- All bug fixes
- All optimizations
- All refactoring

### **Enforcement**:
- **NO CODE** goes into production without peer review
- This rule applies to ALL sessions across ALL projects
- Violations result in session termination

---

## 🧪 **PAIRWISE TESTING - MANDATORY FOR ALL SYSTEMS**

### **Non-Frontend Systems**:
- **Tester AI**: Generates and runs ALL tests (unit, functional, integration, systemic)
- **Reviewer AI**: Ensures ALL tests are created and verifies test output
- **Coverage**: 100% of all functionality must be tested
- **Process**: Tester → Reviewer → Tester iteration until 100% test coverage

### **Frontend Systems (Additional Requirements)**:
- **Playwright Testing**: Full page screenshots of every page
- **Form Testing**: Submit ALL forms, verify ALL responses
- **Email Testing**: Capture ALL emails, verify content, test ALL email links
- **Navigation Testing**: Click ALL links, verify ALL destinations
- **UI Testing**: Verify ALL messaging, redirects, and user flows
- **Secondary Page Testing**: Test ALL forms on secondary pages
- **Coverage**: 100% of UI, forms, emails, navigation, and user flows

### **Enforcement**:
- **100% TEST COVERAGE** is mandatory
- **ALL TESTS MUST PASS** with zero failures
- This rule applies to ALL sessions across ALL projects

---

## 📚 **GLOBAL DOCUMENTATION - MANDATORY FOR REUSABLE COMPONENTS**

### **Rule**: ALL reusable components MUST be documented in Global-Docs folder

### **Applies To**:
- Components that might be reused across projects
- Patterns that could apply to multiple projects
- Solutions that have universal applicability
- Scripts that could be used in other projects

### **Format**:
- Project-agnostic documentation
- Template variables for customization
- Clear usage instructions
- Examples and best practices

### **Location**:
- `Global-Docs/components/` - Reusable components
- `Global-Docs/patterns/` - Reusable patterns
- `Global-Docs/scripts/` - Reusable scripts

### **Enforcement**:
- Documentation is **MANDATORY** for all reusable code
- This rule applies to ALL sessions across ALL projects

---

## 💾 **RESOURCE MANAGEMENT - MANDATORY FOR ALL SESSIONS**

### **Rule**: ALL sessions MUST use local memory system for optimal resource management

### **Actions**:
- Reduce content size as much as possible
- Tightly control memory usage
- Extract facts from verbose logs
- Clear context between milestones
- Monitor session health continuously

### **Scripts**:
- `resource-cleanup.ps1` - Run after every milestone
- `monitor-resources.ps1` - Check session health regularly
- `emergency-flush.ps1` - When session health < 40

### **Health Thresholds**:
- 90-100: EXCELLENT ✅
- 75-89: GOOD ✅
- 60-74: FAIR ⚠️ (run cleanup)
- 40-59: WARNING 🚨 (run aggressive cleanup)
- 0-39: CRITICAL 💀 (emergency flush required)

### **Goal**:
- Maximize session length
- Prevent crashes
- Maintain optimal performance

### **Enforcement**:
- Resource management is **MANDATORY** for all sessions
- This rule applies to ALL sessions across ALL projects

---

## ✅ **100% COMPLETION STANDARDS - MANDATORY FOR ALL SESSIONS**

### **Rule**: "Done" means 100% peer coded AND 100% pairwise tested AND 100% passing tests

### **Prohibited**:
- "Core functionality completed"
- "95% done"
- "Minor bugs remaining"
- "Suggested next steps"
- "Further steps needed"
- "Minor issues to address"

### **Required**:
- EVERYTHING must be peer coded
- EVERYTHING must be pairwise tested
- ALL tests must pass with zero failures
- ZERO bugs, ZERO issues, ZERO incomplete functionality

### **Standard**:
- Zero bugs
- Zero issues
- Zero incomplete functionality
- Zero test failures
- Zero unresolved problems

### **Enforcement**:
- **NO PARTIAL COMPLETIONS** are acceptable
- This rule applies to ALL sessions across ALL projects
- Sessions must continue until 100% completion is achieved

---

## 🔄 **MODEL SWITCHING - MANDATORY FOR ALL SESSIONS**

### **Rule**: Model will be automatically switched if mandatory requirements are violated

### **Triggers**:
- Watchdog command violations
- Peer coding violations
- Testing violations
- Knowledge saving violations
- Resource management violations
- Completion standard violations
- Global documentation violations

### **Model Hierarchy**:
1. **Claude Sonnet 4.5** - Primary model for complex tasks
2. **GPT-4** - Secondary model for peer review
3. **Gemini 2.5 Flash** - Tertiary model for testing
4. **DeepSeek Coder** - Fallback model for coding tasks

### **Switching Process**:
1. **First Violation**: Warning logged, model continues
2. **Second Violation**: Switch to GPT-4
3. **Third Violation**: Switch to Gemini 2.5 Flash
4. **Fourth Violation**: Switch to DeepSeek Coder
5. **Fifth Violation**: Session termination with handoff document

### **Enforcement**:
- **AUTOMATIC SWITCHING** with violation logging
- **SESSION TERMINATION** after maximum violations
- **HANDOFF PREPARATION** for session recovery
- This rule applies to ALL sessions across ALL projects

---

### **Automatic Loading**:
- These rules are automatically loaded at session startup
- No manual configuration required
- Rules apply to ALL active projects

### **Integration Points**:
- Startup script loads all memory systems
- Global rules are automatically applied
- Resource management is automatically initialized
- Watchdog protection is automatically enforced

### **Cross-Project Application**:
- Rules apply to ALL projects automatically
- No project-specific configuration needed
- Consistent enforcement across all sessions

---

## ⚠️ **CRITICAL VIOLATIONS**

### **Session Termination Triggers**:
- Commands executed without watchdog protection
- Code used without peer review
- Testing skipped or incomplete
- Knowledge not saved after learning
- Resource management ignored
- Partial completion reported as "done"

### **Enforcement**:
- **ZERO TOLERANCE** for rule violations
- Sessions must be terminated if rules are violated
- All violations must be logged and reported
- Repeat violations result in system-wide review

---

## 📋 **SUCCESS CRITERIA**

### **Every Session Must Achieve**:
- ✅ ALL commands use watchdog protection
- ✅ ALL learnings saved to memory systems
- ✅ ALL code peer reviewed and approved
- ✅ ALL functionality pairwise tested and passing
- ✅ ALL reusable components documented globally
- ✅ Session resources optimally managed
- ✅ 100% completion with zero exceptions
- ✅ ZERO bugs, ZERO issues, ZERO incomplete functionality

### **No Exceptions**:
- These rules apply to ALL sessions
- These rules apply to ALL projects
- These rules are NON-NEGOTIABLE
- These rules are AUTOMATICALLY ENFORCED

---

**STATUS**: ACTIVE AND MANDATORY  
**PRIORITY**: CRITICAL  
**APPLIES TO**: ALL AI sessions across ALL projects  
**ENFORCEMENT**: AUTOMATIC via startup process
