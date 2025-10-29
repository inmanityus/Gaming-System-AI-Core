# Peer-Based Coding Protocol

## Overview

All new functionality must go through a **peer-based coding review process** using multiple AI models to ensure the highest code quality, minimize bugs, and optimize performance before implementation.

---

## 🎯 When to Use This Protocol

**ALWAYS use for:**
- New feature implementation
- New functions or classes
- New API endpoints
- New components or modules
- Significant refactoring
- Complex business logic
- Security-critical code
- Performance-sensitive code

**Optional for:**
- Minor bug fixes (single line changes)
- Trivial updates (comments, formatting)
- Documentation-only changes

**Default Behavior:** When in doubt, use peer review. It's better to over-review than under-review.

---

## 🔄 The Peer-Based Coding Workflow

### **Stage 1: Primary Coding Model - Initial Implementation**

**Select Primary Coding Model:**
- Choose the best code-generation model available
- Recommended: Claude Sonnet 4.5, GPT-4, Gemini 2.5 Flash, DeepSeek Coder
- Must excel at writing clean, maintainable code

**Primary Model Responsibilities:**
1. **Understand Requirements**
   - Parse user request thoroughly
   - Identify edge cases
   - Consider security implications

2. **Write Initial Implementation**
   - Follow project coding standards
   - Include proper error handling
   - Add inline documentation
   - Write type-safe code
   - Consider performance

3. **Self-Review**
   - Check for obvious bugs
   - Verify logic correctness
   - Ensure completeness

**Output:**
```typescript
// Example output structure
{
  "implementation": "...full code...",
  "rationale": "Explanation of approach",
  "assumptions": ["List of assumptions made"],
  "edge_cases": ["Identified edge cases"],
  "test_considerations": ["What should be tested"]
}
```

---

### **Stage 2: Peer Review Model - Code Review**

**Select Peer Review Model:**
- Choose a DIFFERENT model from the primary
- Must be a top-tier model with strong code understanding
- Recommended alternates:
  - If primary is Claude → Use GPT-4 or Gemini
  - If primary is GPT-4 → Use Claude or DeepSeek
  - If primary is Gemini → Use Claude or GPT-4

**Diversity is Key:** Different models have different strengths and will catch different issues.

**Peer Review Instructions:**

Pass to the review model:
```
You are a senior software engineer conducting a peer code review.
Review the following code for:

1. BUGS AND ERRORS
   - Logic errors
   - Off-by-one errors
   - Null/undefined handling
   - Race conditions
   - Memory leaks

2. SECURITY ISSUES
   - Input validation
   - SQL injection vulnerabilities
   - XSS vulnerabilities
   - Authentication/authorization gaps
   - Sensitive data exposure

3. PERFORMANCE
   - Inefficient algorithms
   - Unnecessary iterations
   - Memory inefficiency
   - Database query optimization
   - Caching opportunities

4. CODE QUALITY
   - Readability
   - Maintainability
   - Following DRY principle
   - Proper separation of concerns
   - Consistent naming conventions

5. ERROR HANDLING
   - Comprehensive error catching
   - Meaningful error messages
   - Proper error propagation
   - Graceful degradation

6. TESTING
   - Testability of code
   - Missing test cases
   - Edge cases not covered

7. BEST PRACTICES
   - Language-specific idioms
   - Framework conventions
   - Industry standards

CODE TO REVIEW:
[Primary model's code]

REQUIREMENTS:
[Original user requirements]

Provide:
- List of issues found (categorized by severity: Critical, High, Medium, Low)
- Specific fixes for each issue
- Optimization suggestions
- Alternative approaches if applicable
- Risk assessment
```

**Peer Review Output:**
```typescript
{
  "issues": [
    {
      "severity": "Critical|High|Medium|Low",
      "category": "Bug|Security|Performance|Quality|Error Handling|Testing",
      "description": "What's wrong",
      "location": "File/function/line reference",
      "fix": "Specific code fix",
      "rationale": "Why this is an issue"
    }
  ],
  "optimizations": [
    {
      "description": "What can be improved",
      "current": "Current code snippet",
      "improved": "Optimized code snippet",
      "benefit": "Performance/readability gain"
    }
  ],
  "alternatives": [
    {
      "approach": "Different implementation strategy",
      "pros": ["Advantages"],
      "cons": ["Disadvantages"],
      "recommendation": "Use if..."
    }
  ],
  "overall_assessment": "Summary of code quality",
  "approval_status": "Approved|Needs Changes|Major Revision Required"
}
```

---

### **Stage 3: Primary Model - Final Check & Integration**

**Primary Model Reviews Peer Feedback:**

1. **Evaluate All Issues**
   - Prioritize by severity
   - Validate each issue
   - Determine if fix is applicable

2. **Apply Fixes**
   - Integrate all Critical/High severity fixes
   - Apply Medium severity fixes where reasonable
   - Consider Low severity suggestions
   - Implement optimizations that don't add complexity

3. **Final Self-Review**
   - Verify fixes don't introduce new issues
   - Ensure code still meets requirements
   - Check for integration conflicts
   - Validate error handling

4. **Prepare Final Implementation**
   - Complete, reviewed code
   - Updated documentation
   - List of changes made
   - Remaining known limitations (if any)

**Final Output:**
```typescript
{
  "final_code": "...complete implementation...",
  "changes_from_review": [
    "Fixed: [description]",
    "Optimized: [description]",
    "Added: [description]"
  ],
  "review_summary": {
    "issues_found": 5,
    "issues_fixed": 5,
    "optimizations_applied": 3
  },
  "confidence_level": "High|Medium",
  "known_limitations": ["Any remaining limitations"],
  "testing_recommendations": ["What to test"]
}
```

---

### **Stage 4: Implementation**

**Deploy the Code:**
- Use the final reviewed code
- Include comprehensive comments from the process
- Add test cases based on review insights
- Document any architectural decisions

**Quality Assurance:**
- Run linters
- Execute existing tests
- Add new tests for new functionality
- Verify edge cases identified during review

---

## 📋 Example Workflow

### **Example: User Request**
> "Create an API endpoint to update user profile with validation"

### **Stage 1: Primary Model (Claude Sonnet 4.5) Writes Code**

```typescript
// apps/api/src/routes/user-profile.ts
export async function updateUserProfile(req: FastifyRequest, res: FastifyReply) {
  const { userId } = req.params;
  const { email, name, bio } = req.body;
  
  // Update user in database
  const result = await db.query(
    'UPDATE users SET email = $1, name = $2, bio = $3 WHERE id = $4',
    [email, name, bio, userId]
  );
  
  return res.send({ success: true });
}
```

**Issues Present:**
- No input validation
- No authentication check
- SQL injection risk (though using parameterized query)
- No error handling
- Email format not validated
- No check if user exists

### **Stage 2: Peer Review (GPT-4) Identifies Issues**

```json
{
  "issues": [
    {
      "severity": "Critical",
      "category": "Security",
      "description": "Missing authentication check - anyone can update any user",
      "fix": "Add middleware to verify req.user.id === userId"
    },
    {
      "severity": "High",
      "category": "Bug",
      "description": "No validation on email format",
      "fix": "Use email validation library or regex"
    },
    {
      "severity": "High",
      "category": "Error Handling",
      "description": "Database errors not caught",
      "fix": "Wrap in try-catch, return appropriate error codes"
    },
    {
      "severity": "Medium",
      "category": "Bug",
      "description": "No check if user exists before update",
      "fix": "Query user first or check affected rows"
    },
    {
      "severity": "Medium",
      "category": "Quality",
      "description": "Name and bio length not validated",
      "fix": "Add max length validation"
    }
  ],
  "optimizations": [
    {
      "description": "Use a validation library like Zod",
      "benefit": "Centralized, type-safe validation"
    }
  ]
}
```

### **Stage 3: Primary Model (Claude) Applies Fixes**

```typescript
// apps/api/src/routes/user-profile.ts
import { z } from 'zod';

const UpdateProfileSchema = z.object({
  email: z.string().email().optional(),
  name: z.string().min(1).max(100).optional(),
  bio: z.string().max(500).optional(),
});

export async function updateUserProfile(
  req: FastifyRequest<{ 
    Params: { userId: string };
    Body: z.infer<typeof UpdateProfileSchema> 
  }>, 
  res: FastifyReply
) {
  try {
    const { userId } = req.params;
    
    // SECURITY: Verify user can only update their own profile
    if (req.user.id !== userId && !req.user.roles.includes('admin')) {
      return res.status(403).send({ error: 'Forbidden' });
    }
    
    // VALIDATION: Validate input
    const validatedData = UpdateProfileSchema.parse(req.body);
    
    // Check if user exists
    const userCheck = await db.query(
      'SELECT id FROM users WHERE id = $1',
      [userId]
    );
    
    if (userCheck.rows.length === 0) {
      return res.status(404).send({ error: 'User not found' });
    }
    
    // Build dynamic update query for only provided fields
    const updates: string[] = [];
    const values: any[] = [];
    let paramCount = 1;
    
    if (validatedData.email) {
      updates.push(`email = $${paramCount++}`);
      values.push(validatedData.email);
    }
    if (validatedData.name) {
      updates.push(`name = $${paramCount++}`);
      values.push(validatedData.name);
    }
    if (validatedData.bio !== undefined) {
      updates.push(`bio = $${paramCount++}`);
      values.push(validatedData.bio);
    }
    
    if (updates.length === 0) {
      return res.status(400).send({ error: 'No fields to update' });
    }
    
    // Update user
    values.push(userId);
    const query = `UPDATE users SET ${updates.join(', ')} WHERE id = $${paramCount}`;
    
    await db.query(query, values);
    
    return res.send({ success: true, message: 'Profile updated' });
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).send({ 
        error: 'Validation failed', 
        details: error.errors 
      });
    }
    
    console.error('Profile update error:', error);
    return res.status(500).send({ error: 'Internal server error' });
  }
}
```

**Changes Applied:**
✅ Added authentication check  
✅ Added Zod validation schema  
✅ Added email format validation  
✅ Added comprehensive error handling  
✅ Added user existence check  
✅ Added length validation for name/bio  
✅ Improved error messages  
✅ Added admin bypass for user updates  

---

## 🎯 Model Selection Matrix

### **Primary Coding Models**

| Model | Strengths | Best For |
|-------|-----------|----------|
| **Claude Sonnet 4.5** | Clean code, great structure, security-aware | General purpose, APIs, full-stack |
| **GPT-4** | Comprehensive, detailed, follows specs | Complex business logic, algorithms |
| **Gemini 2.5 Flash** | Fast, good with modern frameworks | React/Next.js, frontend code |
| **DeepSeek Coder** | Excellent at algorithms, optimization | Performance-critical code, algorithms |

### **Peer Review Models**

| If Primary Is... | Use for Review... | Why |
|-----------------|-------------------|-----|
| Claude Sonnet 4.5 | GPT-4 or Gemini | Different training, catches different patterns |
| GPT-4 | Claude or DeepSeek | Strong security review, performance focus |
| Gemini 2.5 Flash | Claude or GPT-4 | More thorough error handling review |
| DeepSeek Coder | Claude or GPT-4 | Better at catching edge cases |

**Never use the same model for both stages** - defeats the purpose of peer review.

---

## 🔍 Review Checklist

### **Critical Items (Must Check)**
- [ ] Authentication/Authorization
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Error handling
- [ ] Null/undefined handling
- [ ] Type safety

### **High Priority**
- [ ] Edge cases
- [ ] Race conditions
- [ ] Resource leaks
- [ ] Performance bottlenecks
- [ ] Error messages
- [ ] Logging
- [ ] Data consistency

### **Medium Priority**
- [ ] Code readability
- [ ] Documentation
- [ ] Naming conventions
- [ ] DRY principle
- [ ] Code organization
- [ ] Test coverage

### **Nice to Have**
- [ ] Optimization opportunities
- [ ] Alternative approaches
- [ ] Future extensibility
- [ ] Code comments
- [ ] Type definitions

---

## 📊 Quality Metrics

Track the effectiveness of peer review:

```typescript
// .logs/peer-review-metrics.json
{
  "total_reviews": 150,
  "issues_found": {
    "critical": 23,
    "high": 87,
    "medium": 134,
    "low": 67
  },
  "issues_fixed": {
    "critical": 23,  // 100%
    "high": 85,      // 98%
    "medium": 120,   // 90%
    "low": 45        // 67%
  },
  "average_review_time": "5 minutes",
  "bugs_prevented": 23,
  "production_bugs_after_review": 2
}
```

**Success Indicators:**
- Critical issues found: Should trend down over time (code quality improving)
- Critical issues fixed: Should be 100%
- Production bugs after review: Should be minimal

---

## 🚀 Integration with Development Workflow

### **For Cursor/VS Code:**

```typescript
// .cursor/peer-review-workflow.ts
async function peerBasedCoding(userRequest: string) {
  // Stage 1: Primary model writes code
  const primaryModel = 'claude-sonnet-4.5';
  const initialCode = await generateCode(primaryModel, userRequest);
  
  // Stage 2: Different model reviews
  const reviewModel = primaryModel === 'claude-sonnet-4.5' 
    ? 'gpt-4' 
    : 'claude-sonnet-4.5';
  const review = await reviewCode(reviewModel, initialCode, userRequest);
  
  // Stage 3: Primary model applies fixes
  const finalCode = await applyReviewFixes(
    primaryModel, 
    initialCode, 
    review
  );
  
  // Stage 4: Implement
  return finalCode;
}
```

### **Automatic Triggers:**

Configure to automatically trigger peer review for:
- New files created
- Functions > 20 lines
- Security-sensitive code (auth, payment, etc.)
- API endpoints
- Database queries

---

## ⚙️ Configuration

### **`.peer-review-config.json`**

```json
{
  "enabled": true,
  "primary_model": "claude-sonnet-4.5",
  "review_models": {
    "claude-sonnet-4.5": "gpt-4",
    "gpt-4": "claude-sonnet-4.5",
    "gemini-2.5-flash": "claude-sonnet-4.5",
    "deepseek-coder": "gpt-4"
  },
  "auto_trigger": {
    "new_files": true,
    "function_line_threshold": 20,
    "security_keywords": ["auth", "password", "token", "crypto", "payment"],
    "always_review": ["**/routes/**", "**/api/**", "**/auth/**"]
  },
  "logging": {
    "enabled": true,
    "path": ".logs/peer-review/",
    "include_full_code": false
  },
  "quality_gates": {
    "block_on_critical": true,
    "block_on_high_count": 5,
    "warn_on_medium_count": 10
  }
}
```

---

## 📝 Logging Format

Each peer review session should be logged:

```
.logs/peer-review/
  - 2025-10-10T10-30-15-user-profile-update.md
  
Format:
---
# Peer Review: User Profile Update
Date: 2025-10-10 10:30:15
Primary Model: Claude Sonnet 4.5
Review Model: GPT-4

## Requirements
[Original user request]

## Initial Implementation
[Primary model's code]

## Review Findings
- Critical: 1
- High: 2
- Medium: 3
- Low: 1

### Issues
1. [Critical] Missing authentication
2. [High] No input validation
...

## Final Implementation
[Reviewed and fixed code]

## Metrics
- Review time: 3 minutes
- Issues found: 7
- Issues fixed: 7
- Lines of code: 45
```

---

## 🐛 When Bugs Still Happen

If bugs make it to production despite peer review:

1. **Analyze the Failure**
   - Why wasn't it caught?
   - Was it a blind spot for both models?
   - Was it an edge case not considered?

2. **Update Process**
   - Add to review checklist
   - Update model instructions
   - Create test case for similar scenarios

3. **Feed Back to Models**
   - Include in future prompts
   - Update examples
   - Improve review criteria

---

## 🚀 Quick Start

### **For This Project:**

Add to your development workflow:

```bash
# Before implementing new feature
echo "Starting peer-based coding for: $FEATURE_NAME"

# 1. Primary model writes code
# 2. Review model checks code  
# 3. Primary model refines
# 4. Implement with confidence
```

### **For Linux Cursor:**

1. Copy `docs/Peer-Coding.md`
2. Add to `.cursorrules`:
   ```
   Always use peer-based coding for new functionality.
   See docs/Peer-Coding.md for process.
   ```
3. Configure model access (direct + OpenRouter AI MCP)
4. Test with sample feature

---

## 🔄 Version History

- **v1.0** - Initial peer-based coding protocol
- Created: 2025-10-10
- Last Updated: 2025-10-10

---

**Peer-based coding ensures every line of code is reviewed by multiple AI models, catching bugs before they reach production and maintaining consistently high code quality.**





