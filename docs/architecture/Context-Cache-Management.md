# Context & Cache Management Protocol

## Overview

This protocol defines when and how to clear AI context and cache to optimize performance, prevent memory bloat, and maintain fresh perspective while preserving critical project knowledge through **History** and **Reasoning** systems.

---

## 🎯 Core Principles

1. **Clear Between Tasks** - Switch tasks = clear context/cache
2. **Preserve During Tasks** - Same issue = keep context
3. **Never Clear Startup Rules** - System configuration always persists
4. **Maintain Long-Term Memory** - History tracks all past work
5. **Capture Project Logic** - Reasoning stores "why" things work

---

## 🧹 When to Clear Context & Cache

### **✅ CLEAR When:**

1. **Task Switching**
   - Finished working on Feature A, starting Feature B
   - Completed bug fix, moving to new feature
   - Done with admin section, starting client section
   - Finished testing, beginning new implementation

2. **Major Context Shift**
   - Switching from frontend to backend
   - Moving from one module to completely different module
   - Changing from coding to documentation
   - Starting fresh debugging session on different issue

3. **User Requests**
   - "Clear your cache"
   - "Start fresh"
   - "Clear context"
   - Beginning of new session (after long break)

4. **Memory Bloat**
   - Context window getting full
   - Too many files/logs in memory
   - Performance degrading
   - Repeated information causing confusion

### **❌ DO NOT CLEAR When:**

1. **Mid-Task Work**
   - Debugging same issue across multiple files
   - Implementing feature with related changes
   - Running tests and fixing issues from those tests
   - Following logical flow through codebase

2. **Iterative Development**
   - Making changes based on peer review feedback
   - Fixing issues found in end-user testing
   - Refining implementation based on test results
   - Collaborating with other AI models on same problem

3. **Critical Context**
   - Startup rules and configuration
   - Project structure and conventions
   - Security policies
   - Essential protocols (Peer Coding, End-User Testing, etc.)

---

## 📚 History System (Long-Term Memory)

### **Purpose**
Store **completed work** to enable quick retrieval of past efforts on any part of the project without re-reading entire codebase.

### **Storage Location**

**Option 1: Dedicated History Files (Recommended for simplicity)**
```
.project-memory/
  ├── history/
  │   ├── admin-dashboard.md
  │   ├── user-authentication.md
  │   ├── email-system.md
  │   ├── payment-integration.md
  │   └── ai-analysis.md
  └── index.json  # Quick lookup
```

**Option 2: PostgreSQL Database (Recommended for large projects)**
```sql
CREATE TABLE project_history (
  id SERIAL PRIMARY KEY,
  project_name VARCHAR(255) NOT NULL,
  component VARCHAR(255) NOT NULL,
  action_type VARCHAR(50) NOT NULL, -- 'created', 'modified', 'fixed', 'refactored'
  description TEXT NOT NULL,
  files_affected TEXT[], -- Array of file paths
  date_completed TIMESTAMP NOT NULL,
  session_id VARCHAR(100),
  git_commit_hash VARCHAR(40),
  related_issues TEXT[],
  tags TEXT[],
  outcome TEXT, -- 'success', 'partial', 'failed'
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_history_project_component ON project_history(project_name, component);
CREATE INDEX idx_history_tags ON project_history USING gin(tags);
```

### **What to Store**

```json
{
  "component": "Admin User Management",
  "action": "created",
  "date": "2025-10-10",
  "description": "Built complete admin user management system with search, CRUD, bulk actions",
  "files": [
    "apps/web/src/app/admin/users/page.tsx",
    "apps/api/src/routes/admin-users.ts",
    "database-migrations/admin-002-core-admin-tables.sql"
  ],
  "key_decisions": [
    "Used Zod for validation",
    "Implemented row-level security",
    "Added bulk actions for efficiency"
  ],
  "challenges": [
    "JWT token segregation took multiple iterations",
    "Middleware authentication required env variable fix"
  ],
  "outcome": "success",
  "related_tasks": ["admin-dashboard", "authentication"],
  "git_commits": ["abc123", "def456"],
  "testing_completed": true,
  "issues_found": 5,
  "issues_fixed": 5
}
```

### **When to Update History**

- ✅ Feature completed and tested
- ✅ Bug fixed and verified
- ✅ Major refactoring completed
- ✅ End-user testing passed
- ✅ Deployment successful

**Frequency:** After each completed task/feature

---

## 🧠 Reasoning System (Project Logic)

### **Purpose**
Capture the **"why"** behind how the project works - logical flows, business rules, restrictions, design decisions.

### **Storage Location**

**Recommended: Structured Markdown Files**
```
.project-memory/
  ├── reasoning/
  │   ├── authentication-flow.md
  │   ├── form-submissions.md
  │   ├── email-workflows.md
  │   ├── payment-processing.md
  │   ├── user-roles-permissions.md
  │   └── data-flows.md
  └── reasoning-index.md  # Overview
```

**Alternative: PostgreSQL**
```sql
CREATE TABLE project_reasoning (
  id SERIAL PRIMARY KEY,
  project_name VARCHAR(255) NOT NULL,
  topic VARCHAR(255) NOT NULL,
  category VARCHAR(50) NOT NULL, -- 'flow', 'rule', 'restriction', 'decision'
  reasoning TEXT NOT NULL,
  related_components TEXT[],
  confidence DECIMAL(3,2), -- 0.00 to 1.00
  source VARCHAR(50), -- 'user_stated', 'inferred', 'documented'
  last_validated TIMESTAMP,
  conflicts_with INTEGER[], -- IDs of conflicting reasoning
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reasoning_topic ON project_reasoning(project_name, topic);
```

### **What to Store**

```markdown
# Authentication Flow

## How It Works
1. User enters email on login page
2. System sends 6-digit passcode to email
3. Passcode stored in `auth_passcodes` table with 10-minute expiry
4. User enters passcode on verification page
5. System checks if email is admin (via `admin_users` table)
6. System generates appropriate JWT token (admin or extranet)
7. Token stored in cookie and localStorage
8. User redirected to appropriate dashboard

## Why This Way
- Passwordless reduces security risks (no password storage)
- Separate tables enforce admin/extranet segregation
- JWT tokens use different secrets for additional security layer
- 10-minute expiry balances security and UX

## Key Restrictions
- Admin and extranet users CANNOT have same email
- Admin tokens use JWT_ADMIN_SECRET
- Extranet tokens use JWT_EXTRANET_SECRET
- Middleware validates token type matches route
- No password reset flow needed (passwordless)

## Related Components
- `/admin/login` - Admin entry point
- `/login` - Extranet entry point
- `/verify-passcode` - Unified verification
- `middleware.ts` - Token validation
- `auth_passcodes` table - Temporary code storage
- `admin_users` table - Admin authentication
- `users` table - Extranet authentication

## Edge Cases
- Expired passcode → User must request new code
- Wrong passcode → Error message, 3 attempts before rate limit
- Email exists in both tables → INVALID (prevented by DB constraints)
- Token expired → Redirect to login
- Token type mismatch → 403 Forbidden
```

### **Categories of Reasoning**

1. **Logical Flows**
   - User journeys through the system
   - Data flow between components
   - State transitions
   - Conditional branches

2. **Business Rules**
   - "Users can only edit their own profiles unless admin"
   - "Trainers see client requests only after payment"
   - "AI analysis requires intake form completion"

3. **Restrictions**
   - "No duplicate emails across user types"
   - "Videos must be under 2GB"
   - "Passwords must meet complexity requirements"

4. **Design Decisions**
   - "Why we chose PostgreSQL over MongoDB"
   - "Why passwordless instead of traditional auth"
   - "Why separate admin/extranet sections"

5. **Form Workflows**
   - Which form submits to which endpoint
   - What data is required vs optional
   - Where users are redirected after submission
   - What emails are triggered

6. **Permission Matrix**
   - Who can access what
   - Role-based restrictions
   - Feature flags per user type

---

## 🔄 Context Clearing Workflow

### **Step 1: Check If Clearing Is Appropriate**

```typescript
function shouldClearContext(currentTask: string, nextTask: string): boolean {
  // Same task = don't clear
  if (currentTask === nextTask) return false;
  
  // Related tasks (e.g., "fix-user-form" → "test-user-form") = don't clear
  if (areRelatedTasks(currentTask, nextTask)) return false;
  
  // Different tasks = clear
  return true;
}
```

### **Step 2: Save Current Context to History**

Before clearing:
1. Document what was accomplished
2. Save to History system
3. Update Reasoning if logic discovered/changed
4. Commit code changes to git
5. Log completion

### **Step 3: Clear Unnecessary Data**

```bash
# Clear temporary files
rm -rf .logs/temp/*
rm -rf .cache/*

# Clear test artifacts
rm -rf tests/screenshots/*
rm -rf .playwright/

# Clear build artifacts if needed
rm -rf .next/
rm -rf node_modules/.cache/
```

### **Step 4: Preserve Essential Context**

**Always Keep:**
- ✅ `.cursorrules` - Startup rules
- ✅ `.project-memory/` - History and Reasoning
- ✅ Project structure understanding
- ✅ Technology stack knowledge
- ✅ Security policies
- ✅ Coding standards
- ✅ Test protocols
- ✅ Active protocols (Peer Coding, End-User Testing, etc.)

### **Step 5: Load Context for New Task**

When starting new task:
1. Read relevant History entries
2. Load applicable Reasoning
3. Review affected files only
4. Start fresh with clean context

---

## 🔍 Using History & Reasoning

### **Quick Retrieval Example**

**User:** "We need to modify the admin user management"

**AI Process:**
```typescript
// 1. Query History
const history = await getHistory("admin-user-management")
/*
  Returns: When built, files involved, key decisions,
  challenges faced, testing completed, etc.
*/

// 2. Load Reasoning
const reasoning = await getReasoning("user-management-flow")
/*
  Returns: How it works, why designed this way,
  restrictions, edge cases, related components
*/

// 3. Load only affected files
const files = history.files_affected
// Read only those files, not entire codebase

// 4. Start work with focused context
// No need to re-read everything
```

### **Preventing Past Mistakes**

```typescript
// Check History for similar past work
const pastAttempts = await queryHistory({
  component: "authentication",
  action: "modified"
})

// Review challenges and failures
for (const attempt of pastAttempts) {
  if (attempt.outcome === "failed" || attempt.challenges.length > 0) {
    console.log(`Past challenge: ${attempt.challenges}`)
    // Avoid same mistakes
  }
}
```

### **Resolving Reasoning Conflicts**

When conflicting reasoning found:
```markdown
# Reasoning Conflict #47

## Topic: User Profile Editing

### Reasoning A (Source: User stated, 2025-10-05)
"Users can edit their own profiles without restrictions"

### Reasoning B (Source: Code analysis, 2025-10-08)  
"Users can only edit name and bio. Email requires verification. Admin can edit all fields."

### Evidence:
- Code in `apps/api/src/routes/user-profile.ts` shows email validation requirement
- Database trigger prevents direct email updates without verification
- Admin routes have elevated permissions

### Recommendation:
Keep Reasoning B, remove Reasoning A

---

**User Action Required:** Delete line A or B above to resolve
```

---

## 🚀 Implementation

### **Initial Setup**

```bash
# Create directory structure
mkdir -p .project-memory/history
mkdir -p .project-memory/reasoning

# Create index files
touch .project-memory/history/index.md
touch .project-memory/reasoning/index.md

# OR setup PostgreSQL
psql -h localhost -U postgres -d befreefitness -f setup-history-reasoning.sql
```

### **Configuration**

```json
// .project-memory/config.json
{
  "storage_type": "files", // or "postgres"
  "auto_save_history": true,
  "auto_save_reasoning": true,
  "clear_cache_between_tasks": true,
  "preserve_context_for_related_tasks": true,
  "history_retention_days": 365,
  "reasoning_confidence_threshold": 0.7,
  "conflict_resolution_required": true
}
```

### **Integration with Workflows**

```typescript
// At end of task
async function completeTask(taskInfo) {
  // Save to history
  await saveHistory({
    component: taskInfo.component,
    action: taskInfo.action,
    files: taskInfo.files,
    outcome: "success"
  })
  
  // Update reasoning if needed
  if (taskInfo.logicDiscovered) {
    await updateReasoning({
      topic: taskInfo.topic,
      reasoning: taskInfo.logic
    })
  }
  
  // Check for conflicts
  const conflicts = await detectReasoningConflicts()
  if (conflicts.length > 0) {
    await generateConflictReport(conflicts)
  }
  
  // Clear context if switching tasks
  if (taskInfo.isComplete && taskInfo.nextTaskDifferent) {
    await clearCache()
  }
}
```

---

## 📊 Querying History & Reasoning

### **History Queries**

```typescript
// Find all work on authentication
getHistory({ component: "authentication" })

// Find recent failures
getHistory({ outcome: "failed", since: "2025-10-01" })

// Find work on specific file
getHistory({ file: "apps/api/src/routes/admin-users.ts" })

// Get work by session
getHistory({ session_id: "session-123" })
```

### **Reasoning Queries**

```typescript
// Get flow explanation
getReasoning({ topic: "payment-processing-flow" })

// Get all restrictions
getReasoning({ category: "restriction" })

// Get low-confidence reasoning (needs validation)
getReasoning({ confidence_lt: 0.7 })

// Check for conflicts
getReasoning({ has_conflicts: true })
```

---

## ⚠️ Important Notes

### **What Context/Cache Clearing Does NOT Affect:**

- ✅ Startup rules and `.cursorrules`
- ✅ Project configuration
- ✅ History database
- ✅ Reasoning database
- ✅ Git repository
- ✅ Source code
- ✅ Dependencies
- ✅ Environment variables
- ✅ MCP server configurations

### **What Context/Cache Clearing DOES Affect:**

- 🗑️ Temporary conversation context
- 🗑️ Cached file contents in memory
- 🗑️ Intermediate results
- 🗑️ Test artifacts
- 🗑️ Build cache
- 🗑️ Screenshots (unless preserving for issues)
- 🗑️ Temporary logs

---

## 🔄 Maintenance

### **Weekly:**
- Review History entries for completeness
- Validate Reasoning accuracy
- Resolve any conflicts
- Archive old temporary logs

### **Monthly:**
- Audit History coverage (are all components documented?)
- Check Reasoning consistency across related topics
- Update confidence scores based on validations
- Backup History and Reasoning databases

### **Quarterly:**
- Major reasoning review and consolidation
- Remove obsolete reasoning (refactored features)
- Update reasoning for evolved features
- Generate project knowledge report

---

## 🐧 Setup for Linux Cursor

```bash
# 1. Copy documentation
cp docs/Context-Cache-Management.md /path/to/linux/

# 2. Create directories
mkdir -p .project-memory/{history,reasoning}

# 3. Initialize tracking
touch .project-memory/history/index.md
touch .project-memory/reasoning/index.md

# 4. Setup database (if using PostgreSQL)
psql -h localhost -U postgres -d your_db -f setup-history-reasoning.sql

# 5. Add to .cursorrules
echo "# Context Management" >> .cursorrules
echo "Follow Context-Cache-Management.md protocol" >> .cursorrules

# 6. Configure git to ignore cache
echo ".cache/" >> .gitignore
echo ".logs/temp/" >> .gitignore
```

---

## 📚 Related Documentation

- [Collaborate with Other Models](./Collaborate-With-Other-Models.md)
- [Peer-Based Coding](./Peer-Coding.md)
- [End-User Testing](./End-User-Testing.md)

---

## 🔄 Version History

- **v1.0** - Initial context/cache management protocol
- Created: 2025-10-10
- Last Updated: 2025-10-10

---

**Proper context and cache management with History and Reasoning systems enables optimal AI performance, prevents repeated mistakes, and maintains project knowledge across sessions.**





