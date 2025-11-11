# 🤖 REVIEWER MODEL ACCESS - Complete Reference

**Last Updated**: 2025-11-09  
**Status**: ACTIVE - Use for all peer coding and pairwise testing

---

## 🏆 AVAILABLE MODELS (Priority Order)

### **Tier 1: Best Overall Models**

#### 1. **Claude 4.5 Sonnet** (This session's primary model)
- **Access**: Native in Cursor, OpenRouter MCP
- **Best For**: Overall development, architecture, complex reasoning
- **Use**: Primary model for most work

#### 2. **GPT-Codex-2** ⭐ BEST FOR CODING
- **Access**: Direct via `OPENAI_API_KEY`
- **Best For**: Code review, implementation, debugging
- **Use**: Peer review for all code implementations

#### 3. **GPT-5 Pro**
- **Access**: OpenRouter MCP (`openai/gpt-5-pro`), Direct API
- **Best For**: General purpose, reasoning, analysis
- **Use**: Pairwise testing validation, architecture review

#### 4. **Gemini 2.5 Pro**
- **Access**: Direct via `GEMINI_API_KEY`, OpenRouter MCP (`google/gemini-2.5-pro`)
- **Best For**: Complex reasoning, long context, research
- **Use**: Story Teller, architectural decisions, complex analysis

---

## 📋 ACCESS METHODS (Priority Order)

### **Method 1: Direct API Keys** (Preferred - Fastest)
```powershell
# Check if API keys are available
$env:OPENAI_API_KEY  # For GPT-5 Pro, GPT-Codex-2
$env:GEMINI_API_KEY  # For Gemini 2.5 Pro
```

**Advantages**:
- Fastest response times
- No MCP server dependency
- Direct control over model parameters
- More reliable

### **Method 2: OpenRouter MCP Server**
```typescript
// Via OpenRouter MCP
mcp_openrouterai_chat_completion({
  model: "openai/gpt-5-pro" | "google/gemini-2.5-pro",
  messages: [...],
  temperature: 0.7
})
```

**Advantages**:
- Access to many models
- Fallback routing
- Cost tracking
- Model comparison

### **Method 3: Other MCP Servers**
- **Perplexity**: Real-time research, web search
- **Exa**: Code search, documentation search
- **Ref**: Documentation reference

---

## 🎯 USAGE PATTERNS

### **For Code Review** (Peer-Based Coding):
```
Priority: GPT-Codex-2 > GPT-5 Pro > Gemini 2.5 Pro

Process:
1. Claude implements code
2. Send to GPT-Codex-2 for review
3. Fix issues
4. Repeat until approved
```

### **For Test Validation** (Pairwise Testing):
```
Priority: GPT-5 Pro > Gemini 2.5 Pro > GPT-Codex-2

Process:
1. Claude writes and runs tests
2. Send results to GPT-5 Pro for validation
3. Fix coverage gaps
4. Repeat until approved
```

### **For Architecture Decisions**:
```
Priority: Gemini 2.5 Pro > GPT-5 Pro > Claude 4.5

Process:
1. Claude proposes architecture
2. Send to Gemini 2.5 Pro for reasoning
3. Incorporate feedback
4. Finalize design
```

### **For Story/Narrative Design**:
```
Model: Gemini 2.5 Pro (Story Teller)

Process:
1. Send concept to Gemini 2.5 Pro
2. Receive complete narrative design
3. Generate training data
4. Validate lore consistency
```

---

## 🚨 CRITICAL RULES

### **IF MCP/API UNAVAILABLE**:
**STOP IMMEDIATELY and notify user**

**DO NOT**:
- Continue without peer review
- Skip peer review
- Pretend to do peer review
- Use lower-quality fallback models

**User has confirmed**: MCP servers sometimes crash from other projects. If unavailable, ASK FOR HELP.

---

## 🚫 FORBIDDEN MODELS (NEVER USE)

**Outdated Models** (Will give poor results):
- ❌ GPT-4, GPT-4o, GPT-4-turbo (outdated)
- ❌ Claude 3.5 Sonnet, Claude 3.x (outdated)
- ❌ Gemini 1.5 Pro, Gemini 1.x (outdated)
- ❌ DeepSeek V2, V1 (minimum is V3)

**Why Forbidden**: These models are significantly worse than current generation and will:
- Miss critical issues
- Provide outdated suggestions
- Lower overall quality
- Fail to catch subtle bugs

---

## 📊 MODEL SELECTION GUIDE

### **Choose GPT-Codex-2 When**:
- Reviewing code implementation
- Debugging complex issues
- Optimizing algorithms
- Refactoring code
- Security audits

### **Choose GPT-5 Pro When**:
- Validating test coverage
- General-purpose review
- Quick feedback needed
- Architectural analysis
- Performance analysis

### **Choose Gemini 2.5 Pro When**:
- Long context needed (100K+ tokens)
- Complex reasoning required
- Story/narrative design
- Multi-step planning
- Research-heavy tasks

### **Choose Claude 4.5 Sonnet When**:
- As primary implementation model
- For balanced general work
- When context continuity matters
- For user-facing communication

---

## 🔄 INTEGRATION WITH WORKFLOWS

### **Startup Process**:
```powershell
# startup.ps1 should check for API keys
if ($env:OPENAI_API_KEY -and $env:GEMINI_API_KEY) {
    Write-Host "✅ Direct API access available" -ForegroundColor Green
} else {
    Write-Host "⚠️ Using OpenRouter MCP (slower)" -ForegroundColor Yellow
}

# Check OpenRouter MCP availability
try {
    # Test OpenRouter connection
    $testResult = mcp_openrouterai_search_models -limit 1
    Write-Host "✅ OpenRouter MCP available" -ForegroundColor Green
} catch {
    Write-Host "❌ OpenRouter MCP unavailable - STOP if peer review needed" -ForegroundColor Red
}
```

### **Peer Review Function**:
```powershell
function Invoke-PeerReview {
    param([string]$Code, [string]$Context)
    
    # Try Direct API first
    if ($env:OPENAI_API_KEY) {
        return Invoke-GPTCodex2Review -Code $Code -Context $Context
    }
    
    # Fallback to OpenRouter
    if (Test-OpenRouterMCP) {
        return Invoke-OpenRouterReview -Model "openai/gpt-5-pro" -Code $Code
    }
    
    # STOP if neither available
    throw "CRITICAL: No peer review available - STOP WORK"
}
```

---

## 🎯 QUALITY STANDARDS

**Every Peer Review Must**:
1. Be specific about issues (not generic)
2. Provide code examples for fixes
3. Check edge cases and error handling
4. Validate security implications
5. Assess performance impact
6. Verify test coverage
7. Approve only when truly ready

**Reviewer Must Catch**:
- Security vulnerabilities
- Performance bottlenecks
- Edge case bugs
- Mock/fake code
- Invalid tests
- Incomplete implementations
- Poor error handling

---

## 💡 CREATIVE USAGE

**User Encourages**:
- Using models to find efficiencies
- Using models to eliminate bottlenecks
- Creating custom expert models for specific domains
- Training mid-size models for specialized tasks
- Experimenting with model combinations
- Innovative approaches to automation

**Example**: Train a mid-size model specifically for finding optimization opportunities in the codebase.

---

**Integration**: Add to startup.ps1 for automatic availability checking  
**Reference**: Include in all peer-coding and pairwise-testing protocols  
**Enforcement**: MANDATORY for all code and test review

