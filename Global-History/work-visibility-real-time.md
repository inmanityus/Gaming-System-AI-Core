# Work Visibility - Real-Time Command Display
**Date**: January 29, 2025  
**Critical Understanding**: REAL-TIME COMMANDS AND RESULTS

---

## 🚨 CRITICAL CLARIFICATION

**"Show your work in the session window"** means:

### ✅ CORRECT (What User Wants):
- **Show ALL commands as they run**
- **Show command output/results IN REAL-TIME**
- **Display test results as they complete**
- **Show progress updates during work**
- **Display timestamps for operations**
- **Show errors/failures immediately**

### ❌ INCORRECT (What NOT to Do):
- ❌ Just listing files modified at the end
- ❌ Summarizing work after completion
- ❌ Hiding command execution
- ❌ Not showing test results until end
- ❌ Omitting error messages

---

## REQUIRED BEHAVIOR

### For Every Command:
1. **Show the command before executing**
2. **Show output as it streams**
3. **Display results immediately**
4. **Show any errors/failures**
5. **Display progress updates**

### For Every Task:
1. **Show current task at start**
2. **Display commands as they run**
3. **Show test results as they complete**
4. **Display progress percentage updates**
5. **Show next steps clearly**

### For Every Milestone:
1. **Display milestone objectives**
2. **Show all commands during work**
3. **Display results in real-time**
4. **Show progress updates**
5. **Display completion status**

---

## EXAMPLES

### ✅ Good - Real-Time Display:
```
[2025-01-29 14:30:15] Starting Event Bus tests...
[2025-01-29 14:30:16] Running: python -m pytest services/event_bus/tests/ -v
[2025-01-29 14:30:18] Output: test_event_bus.py::test_publish_subscribe PASSED
[2025-01-29 14:30:19] Output: test_event_bus.py::test_multiple_subscribers PASSED
[2025-01-29 14:30:20] Results: 5 passed, 0 failed
[2025-01-29 14:30:21] Event Bus tests complete - all passing
```

### ❌ Bad - Summary Only:
```
Modified files:
- services/event_bus/event_bus.py
- services/event_bus/tests/test_event_bus.py

Tests completed (all passing)
```

---

## IMPLEMENTATION

### Always Use:
- `run_terminal_cmd` with `is_background=false` for visibility
- Display command output immediately
- Show progress updates during long operations
- Display errors immediately when they occur
- Show test results as they stream

### Never:
- Hide command execution
- Summarize after completion only
- Omit error messages
- Skip progress updates
- Hide test failures

---

## ENFORCEMENT

This understanding must be:
1. ✅ Saved to Global-History (this file)
2. ✅ Included in startup process
3. ✅ Referenced at session start
4. ✅ Enforced for all work

---

**Status**: ✅ **UNDERSTANDING CAPTURED - MUST SHOW REAL-TIME COMMANDS**











