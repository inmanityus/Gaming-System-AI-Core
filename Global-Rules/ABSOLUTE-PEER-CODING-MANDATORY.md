# 🚨 ABSOLUTE RULE: PEER CODING & PAIRWISE TESTING MANDATORY

**Status**: ABSOLUTE - NO EXCEPTIONS  
**Enforcement**: MAXIMUM  
**Applies To**: ALL code, ALL tests, ALL features, ALL bug fixes  
**Consequence of Violation**: Project failure

---

## THE MANDATE

**"We get ONE REAL SHOT at blowing people away - otherwise we go away."**

A broken foundation (bugs, vulnerabilities, mock code, invalid tests) WILL DOOM this project. Therefore:

### ABSOLUTE REQUIREMENTS (NOT GUIDELINES):

1. **ALL code must be peer-coded**
   - Primary model (Claude) implements
   - Reviewer model (GPT-5.1 High, GPT-5.1 Codex High, or Gemini 2.5 Pro) reviews
   - Fix issues until approved
   - NO solo coding

2. **ALL tests must be pairwise tested**
   - Tester model creates tests
   - Validator model validates tests
   - Fix until both approve
   - NO untested code

3. **NO mock/fake code**
   - All implementations must be real
   - All backends must be connected
   - All APIs must be functional
   - NO placeholders in production

4. **NO invalid tests**
   - All tests must actually test the code
   - All tests must be comprehensive
   - All tests must pass
   - NO fake passing tests

---

## IMPLEMENTATION

### Access Methods:
1. **OpenRouter MCP**: `mcp_openrouterai_chat_completion`
   - Models: `openai/gpt-5.1`, `openai/gpt-5.1-codex`, `google/gemini-2.5-pro`
   
2. **Direct API Keys**:
   - GPT-5.1 / GPT-5.1 Codex: `OPENAI_API_KEY`
   - Gemini 2.5 Pro: `GEMINI_API_KEY`

### If MCP/API Unavailable:
**STOP IMMEDIATELY** and notify user. Do NOT continue without peer review.

---

## PROCESS

### For New Code:
```
1. Primary model (Claude) implements
2. Send to reviewer model
3. Reviewer provides detailed feedback
4. Primary fixes all issues
5. Repeat until reviewer approves
6. Only then commit code
```

### For Tests:
```
1. Tester model creates comprehensive tests
2. Send to validator model
3. Validator checks test quality and coverage
4. Tester fixes gaps
5. Repeat until validator approves
6. Run tests, all must pass
```

### For Bug Fixes:
```
Same process - NO exceptions for "small" fixes
All fixes must be peer-reviewed
```

---

## WHY THIS IS ABSOLUTE

**The Vision**:
- ALL work done by AI models
- EVERYTHING automated
- Custom expert models for specific tasks
- Leverage MCP tools + custom training
- Beat anything humans could do
- Visual dashboards with AI assistants everywhere

**The Reality**:
- Broken foundation = project failure
- One shot to impress = must be perfect
- No second chances = everything must work
- High stakes = maximum quality required

---

## ENFORCEMENT

- This rule applies to PRIMARY model (Claude Sonnet 4.5) and ALL peer models
- Violations result in restarting the entire implementation
- User has elevated primary model to top position for implementing vision
- This responsibility requires absolute adherence to quality standards

---

**Last Updated**: 2025-11-09  
**Enforcement Level**: ABSOLUTE - NO EXCEPTIONS  
**Applies To**: Every single line of code, every single test  
**Goal**: One shot to blow people away - make it perfect

