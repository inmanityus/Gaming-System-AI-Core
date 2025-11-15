# Context Window Monitoring Rules

## ðŸš¨ CRITICAL RULE - MANDATORY ENFORCEMENT

### **CONTEXT WINDOW THRESHOLD - 60% RULE**

**RULE**: When context window size exceeds 60% of maximum capacity, MANDATORY actions MUST be taken.

**ENFORCEMENT PROCESS**:

1. **Monitor Continuously**: System MUST continuously monitor context window size throughout session
2. **Threshold Detection**: When context exceeds 60% threshold:
   - **IMMEDIATE ACTION**: Execute /clean-session command automatically
   - **NO DELAY**: Cleanup must happen immediately, no waiting for user
   - **NO EXCEPTIONS**: This rule applies to ALL sessions, ALL projects
3. **Post-Cleanup Verification**: After /clean-session completes:
   - **Check Context Again**: Verify context window size after cleanup
   - **If Still > 60%**: Execute /handoff command immediately
   - **Session Transfer**: Create handoff document and transfer to new session
4. **Continuous Monitoring**: Monitoring continues throughout entire session
5. **Automatic Enforcement**: No user input required - system enforces automatically

**THRESHOLD LEVELS**:
- **< 60%**: Normal operation, continue monitoring
- **â‰¥ 60%**: Trigger /clean-session immediately
- **Still â‰¥ 60% after cleanup**: Trigger /handoff immediately

**INTEGRATION**:
- **Startup**: Monitor initialized during startup process
- **During Session**: Continuous monitoring in background
- **Cleanup Integration**: Works with /clean-session command
- **Handoff Integration**: Works with /handoff command

**ENFORCEMENT**:
- **MANDATORY**: This rule is NON-NEGOTIABLE
- **AUTOMATIC**: No user approval required
- **IMMEDIATE**: No delays allowed
- **CONTINUOUS**: Monitoring never stops during session

**PURPOSE**:
- Prevents context bloat
- Maintains session stability
- Ensures optimal performance
- Prevents session crashes from excessive context
