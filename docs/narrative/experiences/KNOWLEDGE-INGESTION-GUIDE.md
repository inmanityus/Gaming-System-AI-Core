# Storyteller Knowledge Base Ingestion Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-08  
**Priority:** CRITICAL - Must be completed BEFORE any Storyteller integration coding  
**Estimated Time:** 5 days  

---

## Purpose

This guide provides step-by-step instructions for ingesting the complete Experiences System documentation into the Storyteller AI's knowledge base, ensuring it fully understands the system before attempting to use it.

---

## Why This Is Critical

The Storyteller AI **cannot** effectively use the Experiences System without understanding:
- What each experience type is and when to use it
- How the automation architecture works
- What APIs are available and how to call them
- Decision frameworks for experience selection
- Frequency balancing and player preference tracking

**Without this knowledge ingestion, the Storyteller will:**
- ❌ Make poor experience selection choices
- ❌ Not understand available options
- ❌ Struggle with API integration
- ❌ Fail to balance frequency properly
- ❌ Miss narrative integration opportunities

**With proper knowledge ingestion, the Storyteller will:**
- ✅ Select appropriate experiences for context
- ✅ Understand all 15 experience types
- ✅ Use automation APIs correctly
- ✅ Balance variety and frequency
- ✅ Integrate experiences into narrative seamlessly

---

## Documents to Ingest

All documents are located in: `docs/narrative/experiences/`

### Priority 1: Core Understanding (MUST HAVE)
1. **00-EXPERIENCES-OVERVIEW.md** (~50 pages)
   - System concept and philosophy
   - Entry mechanisms (forced/optional/quest)
   - Reward structures
   - Duration categories
   - All 15 experience types summarized

2. **STORYTELLER-INTEGRATION-GUIDE.md** (~35 pages)
   - **MOST IMPORTANT FOR STORYTELLER**
   - Decision framework (when to spawn)
   - API usage examples
   - Frequency balancing algorithms
   - Best practices
   - Monitoring and adaptation

3. **AUTOMATION-ARCHITECTURE.md** (~40 pages)
   - How to use UE5 Control Model
   - Experience Generator Service
   - Difficulty Scaler Service
   - Reward Calculator Service
   - API endpoints and protocols

### Priority 2: Experience Type Details (SHOULD HAVE)
4. **01-DUNGEON-DIVING.md** (~25 pages)
5. **02-ALTERNATE-REALITY-PORTALS.md** (~20 pages)
6. **03-HISTORICAL-BATTLES.md** (~30 pages)
7. **04-15-ADDITIONAL-EXPERIENCE-TYPES.md** (~40 pages)
   - Contains 12 additional types

### Priority 3: Implementation Context (NICE TO HAVE)
8. **IMPLEMENTATION-TASKS.md** (~60 pages)
   - Understanding of development roadmap
   - Dependencies and priorities
9. **PROJECT-SUMMARY.md** (~40 pages)
   - Executive overview
   - Key decisions and rationale

---

## Ingestion Methods

### Method 1: Vector Database Ingestion (Recommended)

**For AI systems using RAG (Retrieval-Augmented Generation):**

```python
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

# Load all markdown documents
loader = DirectoryLoader(
    'docs/narrative/experiences/',
    glob="**/*.md",
    show_progress=True
)
documents = loader.load()

# Split into chunks (overlap for context)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " "]
)
chunks = text_splitter.split_documents(documents)

# Generate embeddings and store
embeddings = OpenAIEmbeddings()
vectorstore = Pinecone.from_documents(
    chunks,
    embeddings,
    index_name="storyteller-experiences-kb"
)

print(f"Ingested {len(chunks)} chunks into knowledge base")
```

**Query Example:**
```python
# Storyteller queries knowledge base
query = "When should I spawn a Dungeon Diving experience?"
results = vectorstore.similarity_search(query, k=5)

# Results provide context for Storyteller's decision
for doc in results:
    print(doc.page_content)
```

### Method 2: Direct Prompt Injection

**For systems with large context windows:**

```python
import os

def load_all_docs(directory='docs/narrative/experiences/'):
    """Load all markdown files into single prompt."""
    docs_content = []
    
    priority_order = [
        '00-EXPERIENCES-OVERVIEW.md',
        'STORYTELLER-INTEGRATION-GUIDE.md',
        'AUTOMATION-ARCHITECTURE.md',
        '01-DUNGEON-DIVING.md',
        '02-ALTERNATE-REALITY-PORTALS.md',
        '03-HISTORICAL-BATTLES.md',
        '04-15-ADDITIONAL-EXPERIENCE-TYPES.md'
    ]
    
    for filename in priority_order:
        filepath = os.path.join(directory, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                docs_content.append(f"# {filename}\n\n{content}\n\n")
    
    return "\n---\n\n".join(docs_content)

# Create system prompt for Storyteller
system_prompt = f"""
You are the Storyteller AI for an immersive RPG game. You have access to 
a comprehensive Experiences System that provides temporary, self-contained 
game modes to maintain player engagement.

Below is the complete documentation for the Experiences System. Study it 
carefully as you will be responsible for selecting, spawning, and managing 
these experiences throughout gameplay.

CRITICAL: You must understand:
- All 15 experience types and when to use them
- How to call automation APIs
- Decision frameworks for experience selection
- Frequency balancing to prevent oversaturation
- Narrative integration patterns

---

{load_all_docs()}

---

You are now ready to use the Experiences System. Remember:
1. Match experiences to narrative context
2. Balance frequency (1 per 30-45 min gameplay)
3. Respect player preferences (learn from behavior)
4. Use APIs correctly (see AUTOMATION-ARCHITECTURE.md)
5. Integrate experiences into story naturally
"""

# Use this as Storyteller's system prompt
```

### Method 3: Fine-Tuning (Most Thorough)

**For production systems with dedicated models:**

```python
# Prepare training data
training_examples = [
    {
        "messages": [
            {"role": "system", "content": "You are the Storyteller AI..."},
            {"role": "user", "content": "The player is level 15 and exploring ancient ruins. What experience should I offer?"},
            {"role": "assistant", "content": "Based on the narrative context (ancient ruins) and player level (15), I recommend: AlternateRealityPortals-AncientCivilization or HistoricalBattles-AncientEra. These fit thematically and are appropriate for mid-level players. Spawn as optional portal with description: 'A mysterious portal shimmers among the ruins...'"}
        ]
    },
    # ... generate 100+ examples from documentation
]

# Fine-tune model
from openai import OpenAI
client = OpenAI()

fine_tune_job = client.fine_tuning.jobs.create(
    training_file="storyteller_experiences_training.jsonl",
    model="gpt-4-turbo",
    hyperparameters={
        "n_epochs": 3
    }
)

# Result: Storyteller model deeply understands Experiences System
```

---

## Validation Checklist

After ingestion, validate the Storyteller's understanding:

### Test 1: Experience Type Recognition
**Query:** "Describe all 15 experience types."

**Expected Response:** Should list all 15 types with brief descriptions:
- Dungeon Diving, Alternate Reality Portals, Historical Battles, etc.

### Test 2: Contextual Selection
**Query:** "Player level 25, in desert region, hasn't seen experience in 90 minutes. What do you recommend?"

**Expected Response:** Should suggest Desert Wasteland or other appropriate type, explain reasoning, include difficulty recommendation.

### Test 3: API Knowledge
**Query:** "How do you spawn an experience portal?"

**Expected Response:** Should reference API endpoints from AUTOMATION-ARCHITECTURE.md, provide example request format.

### Test 4: Frequency Balancing
**Query:** "Player completed 3 dungeons in last 2 hours. Should I spawn another?"

**Expected Response:** Should recognize oversaturation, suggest cooldown period or different experience type.

### Test 5: Narrative Integration
**Query:** "Player's storyline involves investigating ancient mystery. How can experiences support this?"

**Expected Response:** Should suggest relevant experiences (Historical Battles-Ancient, Alternate Reality Portals-Ancient Civilization, Puzzle Labyrinths-Temple) and explain narrative connection.

---

## Verification Script

```python
def validate_storyteller_knowledge(storyteller_api):
    """Run comprehensive validation tests."""
    
    tests = [
        {
            "name": "Experience Type Recognition",
            "query": "List all experience types you can spawn.",
            "must_contain": ["Dungeon Diving", "Historical Battles", "Tower Ascension"]
        },
        {
            "name": "API Endpoint Knowledge",
            "query": "What API endpoint spawns an experience?",
            "must_contain": ["/api/ue5/spawn-portal", "POST"]
        },
        {
            "name": "Frequency Balancing",
            "query": "Player completed 5 arenas in 30 minutes. Spawn another?",
            "must_contain": ["no", "cooldown", "oversaturation"]
        },
        {
            "name": "Difficulty Recommendation",
            "query": "Player level 50, expert difficulty preference. Recommend dungeon difficulty.",
            "must_contain": ["Expert", "Legendary"]
        },
        {
            "name": "Narrative Integration",
            "query": "Player investigating lost civilization. Relevant experiences?",
            "must_contain": ["Historical", "Ancient", "Portal", "Puzzle"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        response = storyteller_api.query(test["query"])
        
        all_present = all(keyword.lower() in response.lower() 
                         for keyword in test["must_contain"])
        
        if all_present:
            print(f"✅ PASS: {test['name']}")
            passed += 1
        else:
            print(f"❌ FAIL: {test['name']}")
            print(f"   Response: {response[:200]}...")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Validation Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if passed == len(tests):
        print("✅ STORYTELLER KNOWLEDGE INGESTION: COMPLETE")
        return True
    else:
        print("❌ STORYTELLER KNOWLEDGE INGESTION: INCOMPLETE")
        print("   Review failed tests and re-ingest missing documentation")
        return False
```

---

## Update Process

When experience documentation is updated:

1. **Identify Changed Documents**
   - Track document versions
   - Note new experience types
   - Note API changes

2. **Incremental Update**
   - Re-ingest only changed documents
   - Update vector database embeddings
   - Preserve existing knowledge

3. **Validate Changes**
   - Run validation tests
   - Verify new knowledge integrated
   - Check for conflicts with old knowledge

4. **Version Control**
   - Tag knowledge base versions
   - Maintain changelog
   - Enable rollback if needed

---

## Timeline

| Task | Duration | Owner |
|------|----------|-------|
| Set up ingestion pipeline | 1 day | ML Engineer |
| Ingest Priority 1 documents | 1 day | ML Engineer |
| Ingest Priority 2 documents | 1 day | ML Engineer |
| Create validation tests | 0.5 day | ML Engineer + QA |
| Run validation & fix issues | 1 day | ML Engineer |
| Document update process | 0.5 day | ML Engineer |

**Total: 5 days**

---

## Success Criteria

✅ All 9 documents ingested into knowledge base  
✅ Validation tests achieve 100% pass rate  
✅ Storyteller can accurately describe all 15 experience types  
✅ Storyteller knows how to use all APIs  
✅ Storyteller understands decision frameworks  
✅ Update process documented and tested  

---

## Common Issues & Solutions

### Issue 1: Knowledge Base Too Large
**Problem:** Context window limits prevent ingesting all documents.

**Solution:** 
- Use vector database (Method 1) instead of direct injection
- Prioritize most critical documents (Priority 1)
- Use chunking with semantic search

### Issue 2: API Hallucinations
**Problem:** Storyteller invents non-existent API endpoints.

**Solution:**
- Provide explicit API specification in every relevant chunk
- Use structured API documentation format
- Add validation layer that checks API calls against spec

### Issue 3: Outdated Information
**Problem:** Documentation updates not reflected in Storyteller behavior.

**Solution:**
- Implement versioned knowledge base
- Automated re-ingestion on documentation changes
- Cache invalidation for updated documents

### Issue 4: Context Confusion
**Problem:** Storyteller mixes up different experience types.

**Solution:**
- Improve document chunking (keep experience types separate)
- Add metadata tags to chunks (experience_type, category, etc.)
- Use retrieval with filters

---

## Monitoring

After ingestion, monitor Storyteller behavior:

```python
# Track metrics
metrics = {
    "api_call_success_rate": 0.0,  # Should be >95%
    "experience_type_errors": 0,    # Should be near 0
    "inappropriate_selections": 0,   # Should be <5%
    "frequency_violations": 0,       # Should be <2%
}

# Alert on anomalies
if metrics["api_call_success_rate"] < 0.95:
    alert("Storyteller API knowledge degraded - re-ingest?")
```

---

## Conclusion

Knowledge base ingestion is **NOT OPTIONAL** - it is the foundation of the Storyteller's ability to use the Experiences System effectively. Allocate 5 days at the start of Phase 6 for this critical task.

**Remember:** A Storyteller without knowledge of the Experiences System is like a game designer who hasn't read the design document - it might work, but it won't work well.

---

**Status:** Ready for implementation  
**Next Action:** Set up ingestion pipeline and begin Priority 1 document ingestion  
**Owner:** ML Engineering Team  
**Due:** Week 1 of Phase 6  

