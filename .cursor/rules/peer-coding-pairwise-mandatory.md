# Peer Coding & Pairwise Testing - Mandatory Project Rule

**STATUS**: MANDATORY - ENFORCED AT STARTUP  
**APPLIES TO**: ALL sessions, ALL code, ALL tests  
**NO EXCEPTIONS**: This rule cannot be bypassed

---

## 🚨 CRITICAL REQUIREMENT

**ALL code MUST be peer-reviewed and ALL tests MUST be pairwise-validated. This is enforced at startup and throughout the session.**

---

## STARTUP ENFORCEMENT

When any Cursor AI session starts in this project:

1. **Load This Rule**: This rule is automatically loaded during startup
2. **Display Warning**: Show warning that peer coding and pairwise testing are mandatory
3. **Create Audit Directories**: Ensure `.cursor/audit/code/` and `.cursor/audit/tests/` exist
4. **Verify Mapping System**: Check that `.cursor/mappings/requirements-to-code-mapping.md` exists
5. **Enforce Minimum Models**: Verify all models meet minimum levels before use

**Startup Message**:
```
🚨 MANDATORY RULE ACTIVE 🚨
- Peer-based coding: REQUIRED for ALL code
- Pairwise testing: REQUIRED for ALL tests
- Audit trails: REQUIRED for ALL work
- Minimum model levels: ENFORCED
- Fake/mock code: FORBIDDEN
```

---

## PEER-BASED CODING REQUIREMENTS

### Process (MANDATORY)

1. **Coder Model** writes code
   - Must meet minimum model levels
   - Implements based on unified requirements
   - Ensures code is real, not mock/fake

2. **Reviewer Model** reviews code
   - Different model from different provider
   - Must meet minimum model levels
   - Validates code is real, correct, optimized

3. **Coder** incorporates feedback and finalizes

### Audit Trail

**Location**: `.cursor/audit/code/[filename]-audit.md`

**Required Content**:
- Coder model name and version
- Reviewer model name and version
- Review timestamp
- Review feedback summary
- Changes made based on review
- Final approval status
- Link to requirement(s) being implemented

---

## PAIRWISE TESTING REQUIREMENTS

### Process (MANDATORY)

1. **Tester Model** creates tests
   - Must meet minimum model levels
   - Comprehensive test suite

2. **Reviewer Model** validates tests
   - Different model from different provider
   - Must meet minimum model levels
   - Validates tests are real and test real code

3. **Test Execution**: Both models run tests independently
   - Results must match
   - Non-matches force test re-write

### Audit Trail

**Location**: `.cursor/audit/tests/[testname]-audit.md`

**Required Content**:
- Tester model name and version
- Reviewer model name and version
- Test creation timestamp
- Test execution timestamp
- Test results from both models
- Result comparison
- Final validation status
- Link to code being tested

---

## MINIMUM MODEL LEVELS

**MANDATORY - NO EXCEPTIONS**

- Claude: Minimum 4.5 Sonnet, 4.1 Opus (NO 3.x)
- GPT: Minimum 5, 5-Pro, Codex-2 (NO 4.x, 3.x)
- Gemini: Minimum 2.5 Pro (NO 1.5)
- DeepSeek: Minimum V3 (NO V2, V1)
- Grok: Minimum 4 (NO 3.x)
- Mistral: Minimum 3.1 Medium (NO 1.x)

**Reference**: `Global-Workflows/minimum-model-levels.md`

---

## CODE QUALITY REQUIREMENTS

### Fake/Mock Code Detection

**FORBIDDEN**:
- ❌ Code with `mock`, `fake`, `stub`, `dummy`, `placeholder` in names
- ❌ Code that returns hardcoded values instead of real data
- ❌ Code that simulates behavior instead of real implementation
- ❌ Tests that don't test real code (except unit test mocks)

**EXCEPTIONS**:
- ✅ Hardware simulators when deploying to custom hardware (documented)
- ✅ Unit test mocks for dependencies (integration+ tests must use real code)

### Code Matching to Mappings

**REQUIREMENT**: All code MUST match requirements in the mapping system.

**Process**:
1. Before writing code, check mapping system
2. Identify requirement being implemented
3. Ensure code matches requirement
4. Update mapping after implementation
5. Link code to requirement in audit trail

---

## MAPPING SYSTEM REQUIREMENTS

**Location**: `.cursor/mappings/requirements-to-code-mapping.md`

**Requirements**:
- All requirements must be mapped to code
- All code must be linked to requirements
- Mappings must be updated as code changes
- Missing mappings must be identified and fixed

**Mapping Structure**:
```
REQ-XXX: [Requirement Description]
  └─> Solution: [Solution Document]
      └─> Task: [Task ID]
          └─> Code: [Code Files]
          └─> Tests: [Test Files]
```

---

## ENFORCEMENT

**Automatic Enforcement**:
- Startup script checks this rule is loaded
- Code generation validates peer review occurred
- Test creation validates pairwise validation occurred
- Audit trail creation is mandatory

**Violations**:
- Code without audit trail: BLOCKED
- Tests without audit trail: BLOCKED
- Older generation models: BLOCKED
- Fake/mock code: IDENTIFIED AND FIXED

---

## INTEGRATION WITH /all-rules

This rule integrates with `/all-rules` command:
- Peer-based coding rules enforced
- Pairwise testing rules enforced
- Minimum model levels enforced
- Three-AI review standards applied
- Memory consolidation includes audit trails

---

**END OF MANDATORY RULE**

