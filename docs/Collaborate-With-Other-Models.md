# AI Model Collaboration Protocol

## Overview

When the user says **"collaborate with other models"** or presents a complex task requiring comprehensive solution design, follow this multi-stage AI collaboration workflow to leverage multiple AI models and research tools for optimal results.

---

## 🎯 When to Use This Protocol

- User provides a complex task (e.g., "build a new project", "design a system")
- User explicitly requests "collaborate with other models"
- Task requires comprehensive research, planning, and design
- Solution needs peer review and validation from multiple AI perspectives

---

## 📋 The Collaboration Workflow

### **Stage 1: Research & Information Gathering**

Use the following MCP servers to gather comprehensive information:

1. **Exa MCP** (`mcp_exa_web_search_exa` / `mcp_exa_get_code_context_exa`)
   - Developer-friendly online searches
   - Code-specific context and examples
   - Library/SDK/API documentation

2. **Perplexity Ask MCP** (`mcp_perplexity-ask_perplexity_ask`)
   - Ask questions and receive highly contextualized answers
   - Domain-specific knowledge queries
   - Best practices and industry standards

3. **Ref MCP** (`mcp_Ref_ref_search_documentation` / `mcp_Ref_ref_read_url`)
   - User manuals and service documentation
   - API endpoint explanations
   - Technical specifications

**Research Topics:**
- Best practices for the task domain
- Available tools, libraries, and frameworks
- Common pitfalls and solutions
- Security considerations
- Scalability patterns
- Industry standards

---

### **Stage 2: Director Model - Initial Draft**

**Select the Director Model:**
- Choose the best reasoning/organizational/high-end processing model available
- Recommended: GPT-4, GPT-5-Pro, Claude Sonnet 4.5, or equivalent
- The Director must excel at consolidation and synthesis

**Director's Responsibilities:**
1. Review all research gathered in Stage 1
2. Analyze the user's requirements and goals
3. Create a comprehensive draft solution covering:
   - Architecture and design decisions
   - Implementation approach
   - Technology stack recommendations
   - Security considerations
   - Scalability strategies
   - Testing approach
   - Documentation structure
   - Potential challenges and mitigations

**Output Format:**
- Structured document (markdown or similar)
- Clear sections for each major component
- Rationale for key decisions
- Open questions or areas needing validation

---

### **Stage 3: Multi-Model Peer Review**

**Select Review Models:**

Choose 3-5 diverse AI models from:

**Directly Accessible (Cursor AI Models):**
- GPT-4, GPT-4 Turbo
- Claude Sonnet 3.5, Claude Sonnet 4.5
- Gemini Pro, Gemini 2.5 Flash
- Other available models in Cursor

**Via OpenRouter AI MCP:**
- Anthropic models (Claude variants)
- Google models (Gemini variants)
- Meta models (Llama 3)
- Mistral models
- Perplexity models
- DeepSeek models

**Selection Criteria:**
- Diversity in training and specialization
- Mix of coding-focused and architecture-focused models
- Include at least one specialized model if applicable (e.g., security-focused)

**For Each Review Model:**

Pass the Director's draft along with:
- Original user prompt/requirements
- Research findings summary
- Specific goal statement

**Instruct Each Model To Provide:**

1. **Solution Review**
   - Overall assessment of the approach
   - Alignment with user requirements
   - Technical feasibility

2. **Suggested Changes/Enhancements**
   - Improvements to architecture
   - Better technology choices
   - Optimization opportunities

3. **Issues Discovered**
   - Potential bugs or vulnerabilities
   - Scalability concerns
   - Missing requirements
   - Security gaps

4. **Alternative Ideas**
   - Different architectural approaches
   - Alternative technologies/tools
   - Novel solutions to consider

5. **Research Suggestions**
   - Topics requiring deeper investigation
   - Specific tools/libraries to evaluate
   - Industry patterns to explore

---

### **Stage 4: Research Iteration**

Based on feedback from review models:

1. **Identify Actionable Research Topics**
   - Novel suggestions requiring validation
   - Alternative approaches to investigate
   - Tools/libraries to evaluate

2. **Conduct Additional Research**
   - Use Exa MCP for code examples and technical deep-dives
   - Use Perplexity Ask MCP for expert opinions and best practices
   - Use Ref MCP for detailed documentation

3. **Validate Suggestions**
   - Verify feasibility of alternatives
   - Compare performance characteristics
   - Check compatibility and integration

---

### **Stage 5: Director Consolidation**

**Director Model Reviews:**
- All peer review feedback
- Additional research findings
- Validation results

**Director Creates Updated Solution:**
1. **Incorporate Valid Feedback**
   - Integrate suggested improvements
   - Address identified issues
   - Consider viable alternatives

2. **Resolve Conflicts**
   - When models disagree, synthesize best approach
   - Document trade-offs and reasoning

3. **Enhance Documentation**
   - Add clarifications based on feedback
   - Include alternative approaches (with rationale for choices)
   - Document decisions and trade-offs

**Output:** Updated comprehensive solution document

---

### **Stage 6: Iteration Loop**

**Repeat Stages 3-5 Until:**

- No meaningful new feedback is received
- All major issues are addressed
- Suggestions become redundant or minor
- Solution converges to stable state

**Convergence Criteria:**
- Review models provide only minor suggestions
- No new security/scalability concerns raised
- Alternative suggestions are marginal improvements
- Consensus reached on core architectural decisions

**Typical Iteration Count:** 2-4 rounds

---

### **Stage 7: Final Output**

**Director Model Produces:**

1. **Final Solution Document**
   - Comprehensive, validated design
   - Implementation plan
   - All research and decisions documented
   - Trade-offs and alternatives noted

2. **Implementation Roadmap**
   - Task breakdown
   - Priority ordering
   - Dependency mapping
   - Estimated complexity

3. **Supporting Documentation**
   - Architecture diagrams (if applicable)
   - Technology stack with justification
   - Security checklist
   - Testing strategy
   - Deployment considerations

4. **Research Summary**
   - Key findings from all research
   - Sources and references
   - Industry best practices applied

**Present to User:**
- Clear, actionable solution
- Confidence in approach (validated by multiple models)
- Transparency about trade-offs and alternatives

---

## 🔧 Implementation Notes

### **MCP Server Usage**

```typescript
// Exa - Web Search
mcp_exa_web_search_exa({ query: "Next.js authentication best practices", numResults: 10 })

// Exa - Code Context
mcp_exa_get_code_context_exa({ query: "React useState hook examples", tokensNum: "dynamic" })

// Perplexity Ask
mcp_perplexity-ask_perplexity_ask({ 
  messages: [
    { role: "user", content: "What are the security considerations for JWT authentication?" }
  ]
})

// Ref - Search Documentation
mcp_Ref_ref_search_documentation({ query: "Stripe payment integration typescript" })

// Ref - Read URL
mcp_Ref_ref_read_url({ url: "https://docs.stripe.com/api/authentication" })

// OpenRouter AI - Chat
mcp_openrouterai_chat_completion({
  model: "anthropic/claude-3.5-sonnet",
  messages: [
    { role: "system", content: "You are a senior software architect reviewing a system design." },
    { role: "user", content: "Please review the following architecture..." }
  ]
})
```

### **Model Selection Guidelines**

**Director Model:**
- Highest reasoning capability
- Strong at synthesis and consolidation
- Excellent at technical writing

**Review Models (Select 3-5):**
- **Architecture Specialist:** Claude Sonnet, GPT-4
- **Security Focus:** Specialized security model or GPT-4
- **Performance/Optimization:** Technical specialist model
- **Code Quality:** Programming-focused model
- **Alternative Perspective:** Different AI family for diversity

### **Logging and Tracking**

Track the collaboration process:

```
.logs/collaboration/
  - {timestamp}-research.md         # Research findings
  - {timestamp}-director-draft.md   # Initial solution
  - {timestamp}-review-round-1.md   # First review cycle
  - {timestamp}-review-round-2.md   # Second review cycle
  - {timestamp}-final-solution.md   # Final output
```

---

## 📝 Example Workflow

**User Request:**
> "Build a secure admin dashboard with role-based access control"

**Stage 1 - Research:**
- Exa: Search for "admin dashboard RBAC best practices", "secure authentication patterns"
- Perplexity: Ask "What are the security considerations for admin dashboards?"
- Ref: Find documentation on auth libraries (NextAuth, Passport, etc.)

**Stage 2 - Director Draft:**
- GPT-5-Pro creates comprehensive design document
- Includes: Auth strategy, DB schema, API design, frontend architecture

**Stage 3 - Peer Review:**
- Claude Sonnet 4.5: Reviews architecture, suggests improvements
- Gemini 2.5 Flash: Identifies security gaps
- DeepSeek Coder: Reviews code organization
- GPT-4: Suggests UX enhancements

**Stage 4 - Additional Research:**
- Exa: Research suggested auth library alternatives
- Ref: Review documentation for recommended tools

**Stage 5 - Director Update:**
- GPT-5-Pro incorporates feedback
- Addresses security concerns
- Updates architecture

**Stage 6 - Iteration:**
- Round 2 review: Minor suggestions only
- Convergence achieved

**Stage 7 - Final Output:**
- Comprehensive validated solution
- Implementation roadmap
- All decisions documented

---

## ⚠️ Important Considerations

### **Do Not:**
- Skip research phase
- Use only one model
- Accept first draft without review
- Ignore conflicting feedback without analysis
- Over-iterate on minor details (know when to converge)

### **Do:**
- Use diverse models for review
- Document all decisions and trade-offs
- Conduct thorough research before drafting
- Validate suggestions before incorporating
- Track iterations for transparency

### **Quality Gates:**
- ✅ All research questions answered
- ✅ Multiple models reviewed solution
- ✅ Security validated
- ✅ Scalability considered
- ✅ Trade-offs documented
- ✅ Implementation plan clear
- ✅ Convergence achieved

---

## 🚀 Integration with Cursor Startup

To integrate this protocol into your Cursor startup process:

1. **Add to Cursor Rules:**
   - Reference this document in your `.cursorrules` or similar configuration
   - Define the trigger phrase: "collaborate with other models"

2. **Configure MCP Servers:**
   - Ensure Exa, Perplexity Ask, Ref, and OpenRouter AI MCPs are configured
   - Test connectivity to all required services

3. **Model Access:**
   - Verify access to required AI models
   - Configure OpenRouter AI API key if using MCP

4. **Logging Setup:**
   - Create `.logs/collaboration/` directory
   - Configure logging for transparency

---

## 📚 Related Documentation

- [MCP Servers Overview](./MCP-SERVERS.md)
- [Security Baseline](./Security-Baseline.md)
- [AI Model Selection Guide](./AI-Model-Selection.md)

---

## 🔄 Version History

- **v1.0** - Initial protocol definition
- Created: 2025-10-10
- Last Updated: 2025-10-10

---

**This protocol ensures comprehensive, validated, and peer-reviewed solutions for complex tasks by leveraging the collective intelligence of multiple AI models and extensive research capabilities.**





