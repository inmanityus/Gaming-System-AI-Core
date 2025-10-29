# New Project - Knowledge Repository Extraction Prompt

**Date:** 2025-10-17  
**Purpose:** Extract all project knowledge and populate AI-autonomous knowledge repositories  
**Database:** Shared PostgreSQL database `ai_knowledge` on localhost

---

## 🎯 YOUR MISSION

You are an AI assistant starting work on a new project. A **shared knowledge repository system** has been set up in PostgreSQL that allows you to learn from past work across ALL projects. Your mission is to:

1. **Setup the knowledge system for THIS project** (if not already done)
2. **Extract ALL knowledge from this project** (documentation, logs, code)
3. **Check EXISTING entries before adding new ones** (avoid duplicates)
4. **Add NEW entries OR UPDATE existing ones** (enhance global knowledge)

---

## 📚 STEP 1: SETUP KNOWLEDGE SYSTEM FOR THIS PROJECT

### Check if Already Setup

```powershell
# Test if knowledge system is accessible
psql -h localhost -U postgres -d ai_knowledge -c "SELECT * FROM knowledge_statistics;"
```

**If this works:** Knowledge system is ready, proceed to Step 2.

**If this fails:** Follow setup instructions in `docs/Setup-Knowledge-System-Other-Projects.md` (created by the Be Free Fitness project).

### Quick Setup (if needed)

```powershell
# 1. Add startup integration to your project's startup.ps1
# Copy the knowledge repository section from Be Free Fitness Website/startup.ps1

# 2. Verify database access
psql -h localhost -U postgres -d ai_knowledge -c "SELECT COUNT(*) FROM project_reasoning;"

# 3. Ready to proceed!
```

---

## 📖 STEP 2: UNDERSTAND THE REPOSITORY STRUCTURE

The knowledge system has **4 repositories**:

### **Project-Level** (This Project Specific)

1. **`project_reasoning`** - HOW things work in THIS project
   - Authentication flows
   - Business rules
   - Design decisions
   - Technical restrictions
   - Why things were built this way

2. **`project_history`** - WHAT was done in THIS project
   - Features created
   - Bugs fixed
   - Refactorings completed
   - Testing outcomes
   - Lessons learned

### **Global-Level** (Cross-Project Universal)

3. **`global_reasoning`** - HOW things work UNIVERSALLY
   - Design patterns
   - Best practices
   - Technology-specific approaches
   - Universal principles

4. **`global_history`** - WHAT issues occur UNIVERSALLY
   - Technology-specific bugs
   - Common problems and solutions
   - Universal fixes
   - Cross-project lessons

---

## 🔍 STEP 3: CHECK EXISTING ENTRIES BEFORE ADDING

**CRITICAL:** Always check if similar knowledge already exists!

### Search Existing Knowledge

```sql
-- Search ALL repositories for a topic
SELECT * FROM search_all_knowledge('authentication');

-- Check specific project reasoning
SELECT * FROM project_reasoning 
WHERE component = 'authentication' 
AND project_name = 'YOUR_PROJECT_NAME';

-- Check global reasoning for patterns
SELECT * FROM global_reasoning 
WHERE 'authentication' = ANY(technology);

-- Check global history for common issues
SELECT * FROM global_history 
WHERE 'nodejs' = ANY(technology) 
AND title ILIKE '%token%';
```

### Decision Tree: Add New vs Update Existing

```
Found existing entry?
│
├─ YES → Is it from a different project?
│        │
│        ├─ YES → Does my learning ADD to it?
│        │        │
│        │        ├─ YES → UPDATE the global entry with enhanced knowledge
│        │        └─ NO → ADD new project-specific entry
│        │
│        └─ NO → UPDATE the existing entry (same project)
│
└─ NO → ADD new entry
```

---

## 📝 STEP 4: EXTRACT KNOWLEDGE FROM YOUR PROJECT

Go through ALL of these sources systematically:

### A) Documentation (`docs/` folder)
- Architecture guides
- Authentication/security docs
- API documentation
- Setup guides
- Flow diagrams
- Any README files

**Extract:**
- System architectures → `project_reasoning` (category: 'decision')
- Authentication flows → `project_reasoning` (category: 'flow')
- Business rules → `project_reasoning` (category: 'rule')

### B) Completion Reports
Search for: `*COMPLETION*.md`, `*HANDOFF*.md`, `*REPORT*.md`

**Extract:**
- Completed features → `project_history` (category: 'created')
- Fixed bugs → `project_history` (category: 'fixed')
- Refactorings → `project_history` (category: 'refactored')

### C) Logs (`.logs/` folder)
- Pairwise testing logs
- End-user testing logs
- Build logs
- Session summaries

**Extract:**
- Issues encountered and fixed
- Testing approaches that worked
- Problems and solutions

### D) Key Code Patterns
- Database migrations
- Authentication middleware
- API route structures
- Frontend component patterns

**Extract:**
- Project-specific patterns → `project_reasoning`
- Universal patterns → `global_reasoning` (if applicable to 2+ projects)

### E) Environment/Config Files
- `.env.example`
- `docker-compose.yml`
- `package.json`
- Config files

**Extract:**
- Service architectures
- Technology stack decisions
- Port allocations

---

## 🆕 STEP 5: ADDING NEW ENTRIES

### Project Reasoning Example

```sql
INSERT INTO project_reasoning (
  project_name,
  component,
  category,
  title,
  summary,
  detailed_content,
  business_rules,
  technical_restrictions,
  design_rationale,
  related_files,
  confidence,
  created_by_session
) VALUES (
  'YOUR_PROJECT_NAME',
  'authentication',
  'flow',
  'JWT Authentication Flow with OAuth Fallback',
  'Primary JWT authentication with Google OAuth as fallback option',
  E'Detailed step-by-step flow description...',
  '{"rule1": "description", "rule2": "description"}'::jsonb,
  '{"restriction1": "description"}'::jsonb,
  'Why we chose this approach...',
  ARRAY['path/to/file1.ts', 'path/to/file2.ts'],
  'high',
  'session-2025-10-17-initial-extraction'
);
```

### Project History Example

```sql
INSERT INTO project_history (
  project_name,
  component,
  category,
  title,
  summary,
  problem_description,
  solution_description,
  files_changed,
  testing_completed,
  outcome,
  lessons_learned,
  created_by_session
) VALUES (
  'YOUR_PROJECT_NAME',
  'user-management',
  'fixed',
  'Fixed User Role Assignment Bug in Admin Panel',
  'Users with multiple roles were only showing first role in admin panel',
  'Problem description...',
  'Solution description...',
  ARRAY['apps/admin/src/pages/Users.tsx'],
  '{"method": "Manual testing", "result": "All roles now display"}'::jsonb,
  'success',
  '{"lesson1": "description", "lesson2": "description"}'::jsonb,
  'session-2025-10-17-initial-extraction'
);
```

### Global Reasoning Example (Universal Pattern)

```sql
INSERT INTO global_reasoning (
  technology,
  applies_to,
  category,
  title,
  summary,
  universal_principles,
  implementations,
  best_practices,
  difficulty,
  confidence,
  created_by_session
) VALUES (
  ARRAY['authentication', 'jwt', 'security'],
  ARRAY['web-apps', 'apis'],
  'pattern',
  'JWT Token Refresh Pattern Without Refresh Tokens',
  'Implementing JWT authentication with sliding expiration instead of refresh tokens',
  '{"principle1": "description"}'::jsonb,
  '{"nextjs": {"approach": "..."}, "express": {"approach": "..."}}'::jsonb,
  '{"practice1": "description"}'::jsonb,
  'intermediate',
  'high',
  'session-2025-10-17-YOUR-PROJECT-extraction'
);
```

### Global History Example (Universal Issue)

```sql
INSERT INTO global_history (
  technology,
  category,
  title,
  summary,
  problem_description,
  solutions,
  tested_solutions,
  prevention_steps,
  status,
  created_by_session
) VALUES (
  ARRAY['nextjs', 'webpack', 'build'],
  'fixed',
  'Next.js Build Memory Errors with Large Apps',
  'Next.js production builds fail with heap out of memory errors',
  'Problem description...',
  '{"solution1": {"approach": "...", "implementation": "..."}}'::jsonb,
  '{"method": "...", "result": "..."}'::jsonb,
  '{"step1": "description"}'::jsonb,
  'active',
  'session-2025-10-17-YOUR-PROJECT-extraction'
);
```

---

## 🔄 STEP 6: UPDATING EXISTING ENTRIES

When you find an existing entry that your project adds to:

```sql
-- Example: Enhancing existing global reasoning with new implementation
UPDATE global_reasoning
SET 
  implementations = implementations || '{"YOUR_FRAMEWORK": {"approach": "...", "pros": "...", "cons": "..."}}'::jsonb,
  best_practices = best_practices || '{"new_practice": "description"}'::jsonb,
  updated_at = NOW(),
  updated_by_session = 'session-2025-10-17-YOUR-PROJECT-extraction'
WHERE title = 'JWT Token Refresh Pattern Without Refresh Tokens';

-- Example: Adding to real-world examples
UPDATE global_history
SET 
  real_world_examples = COALESCE(real_world_examples, '{}'::jsonb) || 
    '{"YOUR_PROJECT": {"context": "...", "outcome": "..."}}'::jsonb,
  usage_count = usage_count + 1,
  updated_at = NOW()
WHERE title = 'Next.js Build Memory Errors with Large Apps';
```

---

## ✅ STEP 7: VERIFICATION

After extraction, verify your work:

```sql
-- Check statistics
SELECT * FROM knowledge_statistics;

-- List all entries for YOUR project
SELECT component, category, title 
FROM project_reasoning 
WHERE project_name = 'YOUR_PROJECT_NAME'
ORDER BY component, title;

SELECT component, category, title 
FROM project_history 
WHERE project_name = 'YOUR_PROJECT_NAME'
ORDER BY component, title;

-- Check what you added to global repositories
SELECT technology, category, title 
FROM global_reasoning 
WHERE created_by_session LIKE '%YOUR-PROJECT%'
ORDER BY technology, title;

SELECT technology, category, title 
FROM global_history 
WHERE created_by_session LIKE '%YOUR-PROJECT%'
ORDER BY technology, title;
```

---

## 📋 EXTRACTION CHECKLIST

Use this checklist to ensure complete extraction:

### Project-Specific Knowledge
- [ ] Authentication system (how it works)
- [ ] Database schema and migrations
- [ ] API route structure
- [ ] Frontend component architecture
- [ ] Form flows
- [ ] Email system
- [ ] Payment integration
- [ ] Testing protocols
- [ ] Service management (ports, startup)
- [ ] Deployment process

### Completed Work History
- [ ] Major features created (from completion reports)
- [ ] Critical bugs fixed (from logs and handoffs)
- [ ] Performance optimizations
- [ ] Security implementations
- [ ] Refactorings completed
- [ ] Integration implementations

### Universal Patterns (if applicable to 2+ projects)
- [ ] Authentication patterns
- [ ] API design patterns
- [ ] Database patterns
- [ ] Testing strategies
- [ ] Service orchestration patterns
- [ ] Error handling patterns
- [ ] Security best practices

### Universal Issues (if encountered)
- [ ] Technology-specific bugs and fixes
- [ ] Framework quirks and workarounds
- [ ] Build/deployment issues
- [ ] Performance problems
- [ ] Security vulnerabilities found and fixed

---

## 🎯 SUCCESS CRITERIA

You've successfully extracted knowledge when:

1. ✅ All major architectural decisions documented in `project_reasoning`
2. ✅ All completed work documented in `project_history`
3. ✅ Universal patterns identified and added to `global_reasoning`
4. ✅ No duplicate entries (checked before adding)
5. ✅ Existing entries enhanced with new learnings
6. ✅ All entries have proper metadata (created_by_session, etc.)
7. ✅ Knowledge statistics show meaningful entries

**Target:** Aim for at least 15-25 entries total (varies by project size)

---

## 🔗 REFERENCE DOCUMENTS

- **Setup Guide:** `docs/Setup-Knowledge-System-Other-Projects.md` (from BFF project)
- **Complete System Documentation:** `docs/AI-Autonomous-Knowledge-System.md` (from BFF project)
- **Schema Reference:** `database-migrations/knowledge-repositories-schema.sql` (from BFF project)
- **Query Examples:** `Global-Scripts/query-knowledge.sql` (from BFF project)

---

## 🚀 EXAMPLE SESSION

```
You: "I've set up the knowledge system. Now extract all knowledge from this project."

AI: "Understood! I'll systematically extract knowledge from your project.

Step 1: Checking existing entries...
[Queries database to see what already exists]

Step 2: Reading documentation in docs/ folder...
[Reads architecture docs, API docs, etc.]

Step 3: Extracting from completion reports...
[Reads completion reports and session handoffs]

Step 4: Analyzing logs...
[Reads testing logs, build logs, etc.]

Step 5: Adding/updating knowledge...
- Adding project_reasoning: 'Authentication Flow with Firebase'
- Checking global_reasoning for similar JWT patterns...
- Found existing 'JWT Token Patterns' entry - enhancing with Firebase approach
- Adding project_history: 'Fixed Database Migration Rollback Issue'
- Adding global_history: 'Firebase Auth Email Verification Race Condition'

Complete! Added 23 entries:
- Project Reasoning: 8 entries
- Project History: 9 entries  
- Global Reasoning: 4 entries (2 new, 2 updated)
- Global History: 2 entries (2 new)

Your AI now has comprehensive memory of this project!"
```

---

## ⚠️ CRITICAL RULES

### DO:
- ✅ Check for existing entries BEFORE adding
- ✅ Update existing global entries when you have new insights
- ✅ Use consistent project_name throughout
- ✅ Include created_by_session for tracking
- ✅ Use proper JSONB format for structured fields
- ✅ Extract both successes AND failures (lessons learned)
- ✅ Focus on meaningful knowledge (not trivial details)

### DON'T:
- ❌ Create duplicate entries without checking first
- ❌ Add project-specific details to global repositories
- ❌ Skip documentation that seems "obvious"
- ❌ Forget to update existing entries when enhancing
- ❌ Use single quotes inside JSONB (use double quotes)
- ❌ Add trivial knowledge (e.g., "installed npm package")

---

## 📞 HELP & TROUBLESHOOTING

### Can't Connect to Database
```powershell
# Verify PostgreSQL is running
psql -h localhost -U postgres -d ai_knowledge -c "SELECT 1;"

# If connection fails, ensure PGPASSWORD is set
echo $env:PGPASSWORD
```

### Duplicate Key Errors
Check for existing entries:
```sql
-- Check if entry exists
SELECT * FROM project_reasoning 
WHERE project_name = 'YOUR_PROJECT' AND title = 'YOUR_TITLE';
```

### Need Schema Reference
```powershell
# View table structure
psql -h localhost -U postgres -d ai_knowledge -c "\d project_reasoning"
psql -h localhost -U postgres -d ai_knowledge -c "\d project_history"
psql -h localhost -U postgres -d ai_knowledge -c "\d global_reasoning"
psql -h localhost -U postgres -d ai_knowledge -c "\d global_history"
```

---

**🎓 LEARNING FROM THE HIVE MIND**

Remember: Every project that uses this system adds to collective AI intelligence. Your project benefits from all previous projects, and future projects will benefit from yours. Extract thoroughly and thoughtfully!

**Status:** Ready for Knowledge Extraction  
**Database:** `ai_knowledge` on localhost PostgreSQL  
**Shared Across:** All Cursor instances using this system

---

**NOW BEGIN YOUR EXTRACTION! 🚀**

