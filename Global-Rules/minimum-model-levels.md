# Minimum Model Levels - Global Rule

## Purpose
This rule enforces minimum model levels across all AI providers to ensure the system uses the most advanced models available, preventing downgrades to older, less capable versions.

## Problem Statement
When switching to "other models," the system has been defaulting to older GPT-4 models instead of the newer GPT-5 models that are available both through Cursor's native models and via the OpenRouter AI MCP server. This rule ensures only the latest generation models are used.

## 🏆 CURRENT BEST MODELS (2025-11-03)

**Top Tier Models (Currently Best):**
1. **Grok 4** - #1 on SWE-Bench (75.0%), #1 on GPQA Diamond (87.5%), best for complex codebase navigation
2. **Claude 4.5 Sonnet** - Best overall reasoning, code analysis, and problem-solving
3. **GPT-5.1 Codex High** - Best for coding tasks, specialized code generation and review (UPGRADED from GPT-Codex-2)
4. **GPT-5.1 High** - Excellent general purpose, high-stakes accuracy (UPGRADED from GPT-5)
5. **Gemini 2.5 Pro** - Best for reasoning, math, and scientific tasks

**Direct Access Available:**
- **Grok 4**: Direct access via X_AI_API_KEY (model: `grok-4-latest`)
- **GPT-5.1 Codex High**: Direct access via OPEN_AI_KEY (NOT OpenRouter key) - UPGRADED from GPT-Codex-2
- **GPT-5.1 High**: Direct access via OPEN_AI_KEY - UPGRADED from GPT-5
- **Gemini 2.5 Pro**: Direct access available
- **Claude 4.5**: Available via Cursor native or OpenRouter

**Note**: OPEN_AI_KEY should be added to the global list of available keys and used as another direct model access method, similar to how Gemini 2.5 Pro can be directly accessed.

## Minimum Model Requirements

### Claude (Anthropic)
**Minimum:** 4.5 Sonnet, 4.1 Opus, 4.5 Haiku

**Allowed Models:**
- `anthropic/claude-sonnet-4.5` ✅
- `anthropic/claude-opus-4.1` ✅
- `anthropic/claude-haiku-4.5` ✅
- `anthropic/claude-opus-4` ✅
- `anthropic/claude-sonnet-4` ✅

**Forbidden Models:**
- Any Claude 3.x models ❌
- Claude 3.5 Sonnet ❌
- Claude 3.7 Sonnet ❌

### GPT (OpenAI)
**Minimum:** 5.1, 5.1-High, 5.1-Codex-High (UPGRADED from 5/5-Pro/Codex-2)

**Allowed Models:**
- `openai/gpt-5.1-codex-high` ✅ (CURRENTLY BEST - Coding specialized, UPGRADED from gpt-codex-2)
- `openai/gpt-5.1-high` ✅ (Highest capability, UPGRADED from gpt-5-pro)
- `openai/gpt-5.1` ✅ (Standard)
- `openai/gpt-5.1-mini` ✅ (Lightweight)
- `openai/gpt-5.1-codex` ✅ (Coding specialized)
- `openai/gpt-5-pro` ✅ (Previous 5.0 generation - still acceptable)
- `openai/gpt-5` ✅ (Previous 5.0 generation - still acceptable)
- `openai/gpt-5-codex` ✅ (Previous 5.0 generation - still acceptable)

**Direct Access:**
- **GPT-5.1 Codex High**: Direct access via OPEN_AI_KEY (NOT OpenRouter key)
  - Key: Available in global keys list
  - Usage: Direct OpenAI API calls, not through OpenRouter
  - Best for: Coding tasks, code generation, code review
  - UPGRADED from GPT-Codex-2

**Forbidden Models:**
- GPT-4.0 and older ❌ (BANNED - GPT-5.1 now available!)
- GPT-4o ❌ (BANNED - GPT-5.1 available!)
- GPT-4 Turbo ❌
- GPT-4.1 and older ❌
- Any GPT-3.x models ❌
- GPT-4 variants ❌

**CRITICAL ENFORCEMENT**: DO NOT use GPT-4o, GPT-4, or any model below GPT-5.1 when GPT-5.1-High/GPT-5.1-Codex-High are available. This is a global rule violation.

### Gemini (Google)
**Minimum:** 2.5 Pro

**Allowed Models:**
- `google/gemini-2.5-pro` ✅ (Highest capability)
- `google/gemini-2.5-flash` ✅ (Fast, general purpose)
- `google/gemini-2.5-flash-lite` ✅ (Ultra-fast)
- `google/gemini-2.5-flash-preview-09-2025` ✅ (Latest preview)
- `google/gemini-2.5-flash-lite-preview-09-2025` ✅ (Latest preview)

**Forbidden Models:**
- Gemini 1.5 Pro ❌
- Gemini 1.5 Flash ❌
- Any Gemini 1.x models ❌

### Grok (xAI)
**Minimum:** 4, 4 Fast

**Allowed Models:**
- `x-ai/grok-4` ✅ (Flagship)
- `x-ai/grok-4-fast` ✅ (Fast version)
- `x-ai/grok-code-fast-1` ✅ (Coding specialized)

**Direct Access:**
- **Grok 4**: Direct access via X_AI_API_KEY
  - Model: `grok-4-latest`
  - Endpoint: `https://api.x.ai/v1/chat/completions`
  - Key: Available in global keys list (some projects have their own)
  - Usage: Direct xAI API calls, not through OpenRouter
  - Best for: Complex codebase navigation, multi-file refactoring, reasoning tasks
  - Top performer: 75.0% on SWE-Bench, 87.5% on GPQA Diamond
  
  **Example Usage:**
  ```bash
  curl https://api.x.ai/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $X_AI_API_KEY" \
    -d '{
      "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Your prompt here"}
      ],
      "model": "grok-4-latest",
      "stream": false,
      "temperature": 0
    }'
  ```

**Forbidden Models:**
- Grok 3 ❌
- Grok 3 Mini ❌
- Grok Beta ❌
- Any Grok 1.x models ❌

### DeepSeek (DeepSeek AI)
**Minimum:** V3 (3.1 Terminus, V3.2 Exp, R1 variants)

**Allowed Models:**
- `deepseek/deepseek-v3.1-terminus` ✅ (Advanced reasoning)
- `deepseek/deepseek-v3.2-exp` ✅ (Experimental)
- `deepseek/deepseek-chat-v3.1` ✅ (Standard)
- `deepseek/deepseek-r1` ✅ (Reasoning specialized)
- `deepseek/deepseek-v3` ✅ (V3 minimum)

**Forbidden Models:**
- DeepSeek V2 ❌
- DeepSeek V1 ❌
- Any DeepSeek below V3 ❌
- Older DeepSeek models ❌

### Mistral (Mistral AI)
**Minimum:** 3.1 Medium, Devstral Medium, Devstral Small 1.1

**Allowed Models:**
- `mistralai/mistral-medium-3.1` ✅ (Latest medium)
- `mistralai/devstral-medium` ✅ (Coding focused)
- `mistralai/devstral-small` ✅ (Coding focused, lightweight)
- `mistralai/mistral-medium-3` ✅ (Standard medium)
- `mistralai/codestral-2508` ✅ (Coding specialized)

**Forbidden Models:**
- Mistral Medium 1.x ❌
- Mistral Large ❌
- Older Mistral models ❌

### Qwen (Alibaba)
**Minimum:** 3.x Max, 3.x Plus

**Allowed Models:**
- `qwen/qwen3-max` ✅ (Flagship)
- `qwen/qwen3-plus-2025-07-28` ✅ (Plus variant)
- `qwen/qwen3-coder-plus` ✅ (Coding)
- `qwen/qwen3-235b-a22b` ✅ (Latest large)
- `qwen/qwen3-30b-a3b` ✅ (Mid-size)
- `qwen/qwen3-coder-480b-a35b` ✅ (Coding large)

**Forbidden Models:**
- Qwen 2.x ❌
- Qwen 1.x ❌

### GLM (Z.AI / THUDM)
**Minimum:** 4.5, 4.6

**Allowed Models:**
- `z-ai/glm-4.6` ✅ (Latest)
- `z-ai/glm-4.5` ✅ (Previous)
- `z-ai/glm-4.5-air` ✅ (Air version)
- `z-ai/glm-4.5v` ✅ (Vision)
- `thudm/glm-4.1v-9b-thinking` ✅ (Vision, thinking)

**Forbidden Models:**
- GLM 4.0 and earlier ❌
- GLM 3.x ❌

### Image Generation Models (Specialized)
**IMPORTANT:** When user requests image generation ("generate an image", "create an image", "make an image"), use these specialized models:

**Recommended Models (in order of preference):**
1. **`google/gemini-2.5-flash-image`** ✅ (RECOMMENDED - "Nano Banana")
   - **Best for:** Contextual understanding, image edits, multi-turn conversations
   - **Pricing:** Ultra-cheap ($0.0000003 prompt / $0.0000025 completion per 1K tokens)
   - **Features:** Aspect ratio control, state-of-the-art quality
   - **Status:** Generally available (stable release)
   - **Selection Priority:** Use this for 90% of image generation requests

2. **`openai/gpt-5-image`** ✅ (Premium Quality)
   - **Best for:** Superior instruction following, text rendering, detailed edits
   - **Pricing:** $0.00001 per 1K tokens (both prompt/completion)
   - **Features:** Advanced reasoning + image generation combined
   - **Selection Priority:** Use when user specifically requests premium quality or complex edits

3. **`openai/gpt-5-image-mini`** ✅ (Budget-Friendly)
   - **Best for:** Efficient high-quality generation at lower cost
   - **Pricing:** $0.0000025 prompt / $0.000002 completion per 1K tokens
   - **Features:** Reduced latency, lower cost, still high quality
   - **Selection Priority:** Use when budget concerns are mentioned

**Usage Instructions:**
- Default selection: `google/gemini-2.5-flash-image` for all "generate an image" requests
- Access via OpenRouter AI MCP: `mcp_openrouterai_chat_completion`
- Always verify model availability before generation
- Include image generation parameters in the request

## Model Selection Rules

### Primary Selection Criteria
1. **Capability:** Use the highest capability model available for the task
2. **Generation:** Must be the latest generation (5 for GPT, 4.5/4.1 for Claude, 2.5 for Gemini, 4 for Grok)
3. **Specialization:** Use specialized models when appropriate (e.g., gpt-5-codex for coding)

### Fallback Hierarchy
When a specific model is unavailable, fall back in this order:
1. Latest generation full model
2. Latest generation specialized variant
3. Latest generation lightweight variant
4. DO NOT fall back to previous generation

### Provider Selection
When selecting which provider to use:
1. **Grok 4:** #1 on benchmarks - Best for complex codebase navigation, software engineering, and reasoning (Direct access via X_AI_API_KEY)
2. **Claude 4.5 Sonnet:** Best for complex reasoning, agentic workflows, and extended autonomous tasks
3. **GPT-5.1 Codex High:** Best for coding tasks, specialized code generation and review (UPGRADED - Direct access via OPEN_AI_KEY)
4. **GPT-5.1 High:** Best for general purpose, coding, and high-stakes accuracy (UPGRADED)
5. **Gemini 2.5 Pro:** Best for reasoning, math, and scientific tasks (Direct access available)
6. **DeepSeek V3+:** Best for reasoning and Chinese-language tasks (Minimum V3)
7. **Mistral:** Best for European languages and cost-effective coding
8. **Qwen:** Best for coding and multilingual tasks

## Enforcement

### When Switching Models
- **ALWAYS** use OpenRouter to verify model availability
- **ALWAYS** check model generation number before selection
- **NEVER** accept older generation models
- **NEVER** use GPT-4 when GPT-5 is available
- **NEVER** use Claude 3.x when Claude 4.5+ is available
- **NEVER** use Gemini 1.5 when Gemini 2.5 is available

### Verification Steps
1. Check available models via OpenRouter MCP: `search_models`
2. Filter by provider and generation number
3. Select the appropriate model based on task
4. Verify model ID matches minimum requirements
5. Document model selection in session logs

### Error Handling
If a minimum-level model is unavailable:
1. **STOP** - Do not proceed with an older model
2. **REPORT** - Log why the model is unavailable
3. **ALTERNATE** - Use a different provider with acceptable models
4. **EXPLAIN** - Inform user why model selection changed

## Integration with Other Systems

### Direct API Access (Preferred for Best Models)
**GPT-Codex-2**: Direct access via OPEN_AI_KEY (NOT OpenRouter key)
- **Key Location**: Global keys list (OPEN_AI_KEY)
- **Access Method**: Direct OpenAI API calls
- **Usage**: Use for coding tasks, code generation, code review
- **Key**: `sk-proj-_kr_M010dSlMTovqc78xFGlYEKLeObWPGHuDEX5gJUFSBX0TSyLxqKu3tT0VcWFrw9BHLvmO3FT3BlbkFJsLiQ3kfjg_6Mmm-0imx6rRzOCkfOcXJYhrXYPJW9LidAh1NRkEckYhX5EFh1pihHj0h0myftk`
- **Note**: This key should be added to the global list of available keys

**Gemini 2.5 Pro**: Direct access available (similar pattern)
- Use direct access when available for best performance

### OpenRouter MCP Server
All model searches and selections should go through the OpenRouter MCP server for:
- Model availability verification
- Provider capability checking
- Pricing and context length information
- Latest model discovery

**Exception**: Use direct API access for GPT-Codex-2 (via OPEN_AI_KEY) and Gemini 2.5 Pro when available.

### Cursor Native Models
Cursor's native model switcher should be used when available, but OpenRouter provides a wider selection of specialized models.

### Model Switching Protocol
When user requests "other models" or "different AI models":
1. Determine task requirements (coding, reasoning, speed, cost)
2. Check OpenRouter for available models matching minimum requirements
3. Select appropriate model from allowed list
4. Verify model is latest generation
5. Document selection and reasoning

## Updates and Maintenance

### Review Schedule
- **Monthly:** Review and update minimum model levels
- **Quarterly:** Verify provider model availability
- **Ad-hoc:** Update immediately when new generations released

### Version History
- **2025-11-20:** Added Grok 4 Direct Access
  - Added direct API access details for Grok 4 (`grok-4-latest`)
  - Moved Grok 4 to #1 position in top tier models (75% SWE-Bench, 87.5% GPQA Diamond)
  - Added example curl command for direct xAI API usage
  - Updated provider selection order to reflect benchmark performance

- **2025-11-13:** MAJOR UPDATE - GPT-5.1 Release
  - **UPGRADED**: GPT-5 → GPT-5.1
  - **UPGRADED**: GPT-5 Pro → GPT-5.1 High
  - **UPGRADED**: GPT-Codex-2 → GPT-5.1 Codex High
  - All GPT models now require 5.1 minimum
  - Previous 5.0 models still acceptable during transition

- **2025-10-26:** Initial creation
  - Claude 4.5 Sonnet minimum
  - GPT-5 minimum
  - Gemini 2.5 Pro minimum
  - Grok 4 minimum
  - Added DeepSeek, Mistral, Qwen, GLM

## Related Documentation
- **Universal Model Rankings:** `Global-Docs/Universal-Model-Rankings.md` - **SINGLE SOURCE OF TRUTH** for all model rankings
- **OpenRouter AI MCP Guide:** `Global-Docs/OpenRouter-AI-MCP-Complete-Guide.md` - Complete OpenRouter capabilities
- **OpenRouter MCP:** `/docs/mcp-openrouterai.md`
- **Model Selection Protocol:** `/Global-Workflows/model-selection-protocol.md`
- **AI Collaboration:** `/docs/collaborate-with-other-models.md`

**CRITICAL**: For task-specific model rankings (coding, reasoning, math, science, vision, audio, video), always reference `Global-Docs/Universal-Model-Rankings.md` instead of this file. This file enforces minimum versions; rankings file provides task-specific performance guidance.

---

**Status:** Active  
**Priority:** High  
**Enforcement:** Mandatory  
**Last Updated:** 2025-11-20 (Added Grok 4 Direct Access)

