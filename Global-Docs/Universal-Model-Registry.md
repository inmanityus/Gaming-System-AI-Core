# Universal Model Registry - Single Source of Truth

**Last Updated**: 2025-11-19 (Automated update via /update-models)  
**Purpose**: Consolidated model registry with task-specific rankings, benchmarks, and ALL access methods  
**Authority**: SINGLE SOURCE OF TRUTH - All other files must reference this location  
**Update Command**: `/update-models` (see C:\Users\kento\.cursor\commands\update-models.md)

**CRITICAL**: This is the ONLY file that should contain complete model lists. All other references must point here.

## 🎉 NEW DISCOVERY: Gemini 3 Pro Preview!

**Google has released Gemini 3 Pro Preview** - their latest flagship model!
- 1M token context window
- State-of-the-art multimodal reasoning
- Leading scores on LMArena, GPQA Diamond, MathArena Apex
- Excellent for agentic coding (SWE-Bench Verified, Terminal-Bench 2.0)

**Access**:
- OpenRouter: `google/gemini-3-pro-preview`
- Direct API: Check if available via GEMINI_API_KEY (may be preview-only)

---

## Access Methods - ALL AVAILABLE OPTIONS

### 🔑 Direct API Connections (PRIORITY 1 - Fastest, Most Reliable)

These are direct connections to AI providers. Check your environment variables for API keys:

####

 1. OpenAI Direct API (OPENAI_API_KEY or OPEN_AI_KEY)
**Status**: ✅ AVAILABLE if API key configured  
**Endpoint**: `https://api.openai.com/v1/chat/completions`  
**Models Available**: 20+ models

**Latest Generation:**
- `gpt-5.1` - Latest GPT with adaptive reasoning
- `gpt-5.1-chat` - Fast, lightweight (128K context)
- `gpt-5.1-codex` - Specialized for coding (400K context)
- `gpt-5.1-codex-mini` - Smaller, faster coding model

**Production Models:**
- `gpt-5` - Previous generation (still excellent)
- `gpt-5-pro` - Production-ready flagship
- `gpt-5-codex` - Agentic coding specialist
- `gpt-5-chat` - Conversational

**Legacy (Use only if newer unavailable):**
- `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`
- `gpt-4o`, `gpt-4o-mini`

**Python Example:**
```python
import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-5.1-codex",
    messages=[{"role": "user", "content": "Review this code..."}]
)
```

#### 2. Google/Gemini Direct API (GEMINI_API_KEY) - **ULTRA ACCOUNT**
**Status**: ✅ CONFIGURED by user  
**Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models`  
**Models Available**: 20+ models

**Latest Generation:**
- **`gemini-3-pro-preview`** - **NEWEST FLAGSHIP** (1M context, state-of-the-art multimodal) 🎉
- `gemini-2.5-pro` - State-of-the-art reasoning (#1 on LMArena)
- `gemini-2.5-flash` - Ultra-fast with thinking capabilities (1M context)
- `gemini-2.5-flash-lite` - Ultra-low latency and cost

**Multimodal Specialists:**
- `gemini-2.5-flash-image` ("Nano Banana") - **RECOMMENDED FOR ALL IMAGES**
- `gemini-3-pro-preview` - Native support: text, images, audio, video, code

**Previous Generation:**
- `gemini-1.5-pro`, `gemini-1.5-flash`

**Open-Source (via Google):**
- `gemma-3-27b-it`, `gemma-3-7b-it`, `gemma-3-2b-it`

**Python Example:**
```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use latest Gemini 3 Pro
model = genai.GenerativeModel('gemini-3-pro-preview')
response = model.generate_content("Review this architecture...")

# Or Gemini 2.5 Pro
model25 = genai.GenerativeModel('gemini-2.5-pro')
response25 = model25.generate_content("Reason through this...")
```

#### 3. Anthropic/Claude Direct API (CLAUDE_KEY or ANTHROPIC_API_KEY)
**Status**: ✅ CONFIGURED by user  
**Endpoint**: `https://api.anthropic.com/v1/messages`  
**Models Available**: 12+ models

**Latest Generation:**
- `claude-sonnet-4.5` - Best overall model (1M context, 76.8% SWE-Bench)
- `claude-opus-4` - Maximum capability (72.5% SWE-Bench, best for agents)
- `claude-opus-4.1` - Enhanced version
- `claude-sonnet-4` - 72.7% SWE-Bench, balanced performance
- `claude-haiku-4.5` - Fast, near-frontier quality (73%+ SWE-Bench)

**Previous Generation:**
- `claude-3.5-sonnet`, `claude-3-opus`, `claude-3-haiku`

**Python Example:**
```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_KEY"))
response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Analyze this system..."}]
)
```

#### 4. xAI/Grok Direct API (X_AI_API_KEY or GROK_API_KEY)
**Status**: ✅ AVAILABLE if API key configured  
**Endpoint**: `https://api.x.ai/v1/chat/completions`  
**Models Available**: 5+ models

**Latest Generation:**
- `grok-4` - Top performer (87.5% GPQA, 75% SWE-Bench)
- `grok-3-beta` - Beta testing
- `grok-2.5` - Stable release

**Specialized:**
- `grok-code-fast-1` - 92 t/s coding
- `grok-code-fast-2` - Faster variant

**Python Example:**
```python
import openai  # Compatible API
import os

client = openai.OpenAI(
    base_url="https://api.x.ai/v1",
    api_key=os.getenv("X_AI_API_KEY")
)
response = client.chat.completions.create(
    model="grok-4",
    messages=[{"role": "user", "content": "Analyze..."}]
)
```

#### 5. DeepSeek Direct API (DEEP_SEEK_KEY)
**Status**: ✅ CONFIGURED by user  
**Endpoint**: `https://api.deepseek.com/v1/chat/completions`  
**Models Available**: 15+ models

**Latest Generation:**
- `deepseek-chat-v3` - Latest chat model
- `deepseek-v3.1-terminus` - Production coding (671B params, 37B active)
- `deepseek-v3.2-exp` - Experimental sparse attention
- `deepseek-r1` - Reasoning specialist (MIT licensed!)
- `deepseek-r1t-chimera` - R1 + V3 merge

**Python Example:**
```python
import openai  # Compatible API
import os

client = openai.OpenAI(
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEP_SEEK_KEY")
)
response = client.chat.completions.create(
    model="deepseek-chat-v3",
    messages=[{"role": "user", "content": "Code review..."}]
)
```

#### 6. Moonshot/Kimi Direct API (MOONSHOT_API_KEY)
**Status**: ✅ CONFIGURED by user  
**Endpoint**: `https://api.moonshot.cn/v1/chat/completions`  
**Models Available**: 10+ models

**Latest Generation:**
- `kimi-k2-thinking` - Trillion-param MoE, 200-300 tool calls
- `kimi-k2-0905` - 256K context, improved agentic coding  
- `kimi-linear-48b-a3b-instruct` - 75% KV cache reduction, 6x throughput, 1M context
- `kimi-dev-72b` - 60.4% SWE-Bench Verified

**Python Example:**
```python
import openai  # Compatible API
import os

client = openai.OpenAI(
    base_url="https://api.moonshot.cn/v1",
    api_key=os.getenv("MOONSHOT_API_KEY")
)
response = client.chat.completions.create(
    model="kimi-k2-thinking",
    messages=[{"role": "user", "content": "Complex multi-step task..."}]
)
```

#### 7. NVIDIA/NIM Direct API (NVIDIA_API_KEY)
**Status**: ✅ CONFIGURED by user  
**Endpoint**: `https://integrate.api.nvidia.com/v1`  
**Models Available**: 15+ models

**Latest Generation:**
- `nvidia/nemotron-nano-12b-v2-vl` - Video + document intelligence (hybrid Transformer-Mamba)
- `nvidia/llama-3.3-nemotron-super-49b-v1.5` - 97.4% MATH500, 87.5% AIME-2024
- `nvidia/llama-3.1-nemotron-ultra-253b-v1` - 128K context reasoning
- `nvidia/nemotron-nano-9b-v2` - Unified reasoning/non-reasoning

**Python Example:**
```python
import openai  # Compatible API
import os

client = openai.OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)
response = client.chat.completions.create(
    model="nvidia/llama-3.3-nemotron-super-49b-v1.5",
    messages=[{"role": "user", "content": "Solve this math problem..."}]
)
```

#### 8. Z.AI/GLM Direct API (GLM_KEY)
**Status**: ✅ CONFIGURED by user  
**Endpoint**: `https://open.bigmodel.cn/api/paas/v4/chat/completions`  
**Models Available**: 10+ models

**Latest Generation:**
- `glm-coding-max` - Specialized for code generation
- `glm-4-plus` - Latest flagship (128K context)
- `glm-4-flash` - Fast variant
- `glm-4-0520` - Stable release

**Python Example:**
```python
import openai  # Compatible API
import os

client = openai.OpenAI(
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.getenv("GLM_KEY")
)
response = client.chat.completions.create(
    model="glm-coding-max",
    messages=[{"role": "user", "content": "Generate optimized code..."}]
)
```

#### 9. Azure AI Foundry (AZURE_API_KEY)
**Status**: ✅ CONFIGURED by user  
**Endpoint**: `https://kento-mhckgcc6-eastus2.services.ai.azure.com/api/projects/kento-mhckgcc6-eastus2_project`  
**Models Available**: 100+ models from multiple providers

**Providers Available via Azure:**
- **OpenAI**: GPT-4 Turbo, GPT-3.5-Turbo, text-embedding-ada-002
- **Meta**: Llama-2-7b/13b/70b, Llama-3-8b/70b, Llama-3.1-8b/70b/405b
- **Mistral**: Mistral-Large, Mistral-Small, Mixtral-8x7B
- **Cohere**: Command-R+, Command-R, Embed-v3
- **AI21**: Jamba-1.5-Large, Jamba-1.5-Mini
- **Microsoft**: Phi-4-Multimodal (5.6B), Phi-3-Medium, Phi-3-Mini

**Python Example:**
```python
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import os

endpoint = "https://kento-mhckgcc6-eastus2.services.ai.azure.com/api/projects/kento-mhckgcc6-eastus2_project"
client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(os.getenv("AZURE_API_KEY"))
)

response = client.complete(
    messages=[{"role": "user", "content": "Analyze..."}],
    model="meta-llama-3-1-405b-instruct"  # Or any Azure-hosted model
)
```

**Advantages:**
- Enterprise-grade hosting with SLAs
- Azure integration (Functions, Logic Apps, Key Vault, etc.)
- Private network deployment options
- Compliance certifications (SOC 2, HIPAA, etc.)
- Content filtering and safety

#### 10. Perplexity Direct (PERPLEXITY_API_KEY)
**Status**: ✅ CONFIGURED (via Cursor MCP)  
**Endpoint**: `https://api.perplexity.ai/chat/completions`  
**Models Available**: 3+ models

**Latest Generation:**
- `sonar-pro-search` - Agentic multi-step reasoning + web search ($18 per 1000 requests)
- `sonar-pro` - Advanced reasoning
- `sonar` - Standard model

**Access via MCP:**
```typescript
mcp_perplexity-ask_perplexity_ask({
  messages: [{role: "user", content: "Research question..."}]
})
```

### 🌐 OpenRouter MCP Server (PRIORITY 2 - Maximum Flexibility)

**Status**: ✅ ALWAYS AVAILABLE via Cursor MCP  
**Models**: 500+ from 60+ providers  
**Advantage**: Single API for ALL providers

**MCP Tools:**
```typescript
// Chat completion
mcp_openrouterai_chat_completion({
  model: "openai/gpt-5.1",  // or any provider/model
  messages: [...]
})

// Search models
mcp_openrouterai_search_models({
  query: "coding",
  capabilities: { tools: true },
  limit: 10
})

// Get model info
mcp_openrouterai_get_model_info({
  model: "google/gemini-2.5-pro"
})

// Validate model
mcp_openrouterai_validate_model({
  model: "anthropic/claude-sonnet-4.5"
})
```

**Top Models via OpenRouter:**
- **NEW**: `google/gemini-3-pro-preview` - Latest Gemini (1M context, SOTA multimodal!) 🎉
- `openai/gpt-5.1` - Latest GPT (400K context)
- `openai/gpt-5.1-codex` - Latest GPT for coding (78.2% SWE-Bench)
- `anthropic/claude-sonnet-4.5` - Latest Claude (1M context, 76.8% SWE-Bench)
- `x-ai/grok-4-fast` - **NEW**: 2M context, ultra-cheap 🚀
- `x-ai/grok-4` - Latest Grok reasoning
- `deepseek/deepseek-v3.1-terminus` - Latest DeepSeek production
- `meta-llama/llama-4-scout` - **NEW**: 10M context! 🤯
- `meta-llama/llama-4-maverick` - **NEW**: 400B MoE multimodal
- `moonshotai/kimi-k2-thinking` - **NEW**: Trillion-param MoE, 200-300 tool calls
- `moonshotai/kimi-linear-48b-a3b-instruct` - **NEW**: 6x throughput, 1M context
- `minimax/minimax-m2` - **NEW**: Compact agentic, ultra-cheap
- `kwaipilot/kat-coder-pro:free` - **NEW**: 73.4% SWE-Bench, **FREE**
- `nvidia/llama-3.3-nemotron-super-49b-v1.5` - **NEW**: 97.4% MATH500
- `openrouter/sherlock-dash-alpha` + `sherlock-think-alpha` - **NEW**: 1.8M context, FREE
- `deepcogito/cogito-v2.1-671b` - **NEW**: Strongest open model, RL-trained
- `amazon/nova-premier-v1` - **NEW**: 1M AWS multimodal

### 💻 Ollama (Local Models - PRIORITY 3)

**Status**: ✅ AVAILABLE if Ollama installed  
**Cost**: FREE (runs locally)  
**Privacy**: Complete (no data sent to cloud)

**Popular Models (auto-downloadable):**
```bash
# Coding specialists
ollama pull qwen2.5-coder:32b
ollama pull deepseek-coder-v2:236b
ollama pull codellama:70b

# General purpose
ollama pull llama3.3:70b
ollama pull mistral-large:123b
ollama pull qwen2.5:72b

# Lightweight
ollama pull phi4:14b
ollama pull gemma2:27b
```

---

## Task-Specific Rankings (Benchmarked)

### 🖥️ **CODING** (SWE-Bench Verified)

**Benchmark**: Real-world software engineering across GitHub repos  
**Source**: Independent evaluations + Perplexity research (November 2025)  
**Metric**: % of real-world bugs/features correctly implemented

**Top 10 Models:**

1. **GPT-5.1 / GPT-5.1-Codex** - 78.2% | **BEST OVERALL CODING** 🏆
   - **OpenRouter**: `openai/gpt-5.1` or `openai/gpt-5.1-codex`
   - **Direct API**: OPENAI_API_KEY → `gpt-5.1-codex`
   - **Cost**: $1.25/$10 per 1M tokens
   - **Context**: 400K
   - **HumanEval**: 92.1%
   - **Best for**: Agentic coding, multi-hour runs, production code
   - **New**: GPT-5.1-Codex optimized for coding workflows (+5% vs GPT-5)

2. **Claude Sonnet 4.5** - 76.8% | **Best for Agents & Enterprise**
   - **OpenRouter**: `anthropic/claude-sonnet-4.5`
   - **Direct API**: ANTHROPIC_API_KEY → `claude-sonnet-4.5`
   - **Cost**: $3/$15 per 1M tokens
   - **Context**: 1M tokens
   - **HumanEval**: 91.3%
   - **Best for**: Real-world agents, sustained multi-step reasoning

3. **Gemini 2.5 Pro** - 75.4% | **Excellent Multimodal Coding**
   - **OpenRouter**: `google/gemini-2.5-pro`
   - **Direct API**: GEMINI_API_KEY → `gemini-2.5-pro`
   - **Context**: 1M tokens
   - **HumanEval**: 90.6%
   - **Best for**: Multimodal coding, deep think mode

4. **Grok 4.1** - 74.1% | **Emotionally Intelligent Coding**
   - **OpenRouter**: `x-ai/grok-4.1` or `x-ai/grok-4`
   - **Direct API**: X_AI_API_KEY → `grok-4.1`
   - **HumanEval**: 89.7%
   - **Best for**: Creative problem-solving, innovative solutions

5. **DeepSeek V3** - 73.8% | **Best Open-Source**
   - **OpenRouter**: `deepseek/deepseek-chat-v3` or `deepseek/deepseek-v3.1-terminus`
   - **Direct API**: DEEPSEEK_API_KEY → `deepseek-chat-v3`
   - **Ollama**: `deepseek-coder-v2:236b`
   - **HumanEval**: 89.2%
   - **License**: MIT (fully open!)
   - **Best for**: Cost-effective, privacy-sensitive coding

6. **Claude Haiku 4.5** - 73%+ | **Fastest Frontier-Level**
   - **OpenRouter**: `anthropic/claude-haiku-4.5`
   - **Direct API**: ANTHROPIC_API_KEY → `claude-haiku-4.5`
   - **Speed**: Exceptionally fast
   - **HumanEval**: ~90%
   - **Best for**: Real-time coding, sub-agents, parallel execution

7. **KAT-Coder-Pro V1** - 73.4% | **FREE Agentic Coding** 🆓
   - **OpenRouter**: `kwaipilot/kat-coder-pro:free`
   - **Cost**: $0 (completely free!)
   - **Best for**: Budget-conscious agentic coding

8. **Qwen3-235B / 32B** - 72.9% | **Multilingual Specialist**
   - **OpenRouter**: `qwen/qwen3-coder` or `qwen/qwen3-vl-30b-a3b-thinking`
   - **Ollama**: `qwen2.5-coder:32b`
   - **HumanEval**: 88.5%
   - **Best for**: Multilingual code, enterprise deployments

9. **Kimi K2 Thinking** - High Performance | **Long-Horizon Agentic**
   - **OpenRouter**: `moonshotai/kimi-k2-thinking`
   - **Context**: 256K
   - **Best for**: Persistent step-by-step reasoning, 200-300 tool calls

10. **MiniMax M2** - Strong Performance | **Compact Efficiency**
    - **OpenRouter**: `minimax/minimax-m2`
    - **Cost**: $0.000255/$0.00102 per 1M tokens (ultra-cheap!)
    - **Best for**: Fast inference, high concurrency, cost efficiency

6. **GPT-5.1-Codex** - Specialized | **Agentic Coding**
   - **OpenRouter**: `openai/gpt-5.1-codex` or `openai/gpt-5-codex`
   - **Direct API**: OPENAI_API_KEY
   - **Best for**: Multi-hour coding runs, structured code reviews

7. **Qwen3-Coder-480B** - High Performance | **Open-Source Specialist**
   - **OpenRouter**: `qwen/qwen3-coder`
   - **Ollama**: Not available (too large)
   - **Best for**: Tool use, agentic coding

8. **Devstral Medium** - 61.6% | **Cost-Effective Enterprise**
   - **OpenRouter**: `mistralai/devstral-medium`
   - **Cost**: Budget-friendly
   - **Best for**: Enterprise coding at scale

9. **DeepSeek-Coder-V2** - Competitive | **Open-Source**
   - **OpenRouter**: `deepseek/deepseek-coder-v2`
   - **Ollama**: `deepseek-coder-v2:236b`
   - **License**: MIT (fully open)
   - **Best for**: Local coding, privacy-sensitive

10. **Llama 3.3 70B** - Good Performance | **Free & Open**
    - **OpenRouter**: `meta-llama/llama-3.3-70b-instruct`
    - **Ollama**: `llama3.3:70b`
    - **License**: Llama 3 (permissive)
    - **Best for**: Local/offline coding

---

### 🧠 **REASONING** (GPQA Diamond)

**Benchmark**: Graduate-level science & reasoning questions  
**Source**: Independent benchmark + Perplexity research (November 2025)  
**Metric**: % correct on expert-level questions

**Top 10 Models:**

1. **Gemini 3 Pro Preview** - 90%+ (estimated) | **NEW DISCOVERY** 🎉
   - **OpenRouter**: `google/gemini-3-pro-preview`
   - **Direct API**: GEMINI_API_KEY → `gemini-3-pro-preview` (may require early access)
   - **Context**: 1M tokens
   - **Best for**: State-of-the-art multimodal reasoning, agentic workflows
   - **Description**: Google's flagship frontier model, leading scores on LMArena, GPQA Diamond, MathArena Apex

2. **Claude Sonnet 4.5** - 73.1% | **Best for Enterprise**
   - **OpenRouter**: `anthropic/claude-sonnet-4.5`
   - **Direct API**: ANTHROPIC_API_KEY → `claude-sonnet-4.5`
   - **Context**: 1M tokens
   - **AIME 2025**: 85.7%

3. **GPT-5.1** - 72.5% | **Adaptive Reasoning**
   - **OpenRouter**: `openai/gpt-5.1`
   - **Direct API**: OPENAI_API_KEY → `gpt-5.1`
   - **Context**: 400K tokens
   - **AIME 2025**: 86.4%

4. **Gemini 2.5 Pro** - 71.8% | **Multimodal Reasoning**
   - **OpenRouter**: `google/gemini-2.5-pro`
   - **Direct API**: GEMINI_API_KEY → `gemini-2.5-pro`
   - **Context**: 1M tokens
   - **AIME 2025**: 84.9%

5. **Grok 4.1** - 70.9% | **Emotionally Intelligent**
   - **OpenRouter**: `x-ai/grok-4.1` or `x-ai/grok-4`
   - **Direct API**: X_AI_API_KEY → `grok-4.1`
   - **AIME 2025**: 83.2%

6. **DeepSeek V3** - 70.5% | **Best Open-Source**
   - **OpenRouter**: `deepseek/deepseek-chat-v3`
   - **Direct API**: DEEPSEEK_API_KEY → `deepseek-chat-v3`
   - **Ollama**: `deepseek-r1` (reasoning specialist)
   - **AIME 2025**: 82.6%
   - **License**: MIT

7. **Kimi K2 Thinking** - High Performance | **Long-Horizon**
   - **OpenRouter**: `moonshotai/kimi-k2-thinking`
   - **Context**: 256K tokens
   - **Best for**: 200-300 step agentic workflows

8. **Qwen3-235B** - 69.8% | **Multilingual Reasoning**
   - **OpenRouter**: `qwen/qwen3-vl-235b-a22b-thinking`
   - **AIME 2025**: 81.9%

9. **Deep Cogito V2.1 671B** - State-of-the-Art | **Open Model**
   - **OpenRouter**: `deepcogito/cogito-v2.1-671b`
   - **Description**: One of strongest open models globally, RL-trained

10. **Amazon Nova Premier** - High Performance | **AWS Integration**
    - **OpenRouter**: `amazon/nova-premier-v1`
    - **Context**: 1M tokens
    - **Best for**: AWS deployments, teaching distillation

4. **Grok 3 [Beta]** - 84.6%
   - **OpenRouter**: `x-ai/grok-3-beta`
   - **Direct API**: X_AI_API_KEY

5. **OpenAI o3** - 83.3%
   - **OpenRouter**: `openai/o3`
   - **Direct API**: OPENAI_API_KEY

6. **Claude Sonnet 4.5** - 82%+ (estimated)
   - **OpenRouter**: `anthropic/claude-sonnet-4.5`
   - **Direct API**: ANTHROPIC_API_KEY

7. **DeepSeek-R1** - 79.8%
   - **OpenRouter**: `deepseek/deepseek-r1`
   - **Direct API**: DEEPSEEK_API_KEY
   - **License**: MIT (open-source!)

8. **Claude Opus 4.1** - High Performance
   - **OpenRouter**: `anthropic/claude-opus-4.1`
   - **Direct API**: ANTHROPIC_API_KEY

9. **Gemini 2.5 Flash** - Fast Reasoning
   - **OpenRouter**: `google/gemini-2.5-flash`
   - **Direct API**: GEMINI_API_KEY

10. **Qwen3-235B-Thinking** - Open-Source
    - **OpenRouter**: `qwen/qwen3-vl-235b-a22b-thinking`
    - **Ollama**: Not available (too large)

---

### 🔢 **MATHEMATICS** (AIME 2025)

**Benchmark**: High school-level math competition  
**Source**: Official AIME results (2025)  
**Metric**: % problems solved correctly

**Top 10 Models:**

1. **GPT-5.1** - 100% (Perfect Score!)
   - **OpenRouter**: `openai/gpt-5.1`
   - **Direct API**: OPENAI_API_KEY

2. **GPT-oss-20b** - 98.7%
   - **OpenRouter**: `openai/gpt-oss-20b`
   - **Direct API**: OPENAI_API_KEY

3. **OpenAI o3** - 98.4%
   - **OpenRouter**: `openai/o3`
   - **Direct API**: OPENAI_API_KEY

4. **GPT-oss-120b** - 97.9%
   - **OpenRouter**: `openai/gpt-oss-120b`
   - **Direct API**: OPENAI_API_KEY

5. **Claude Haiku 4.5** - 96.3%
   - **OpenRouter**: `anthropic/claude-haiku-4.5`
   - **Direct API**: ANTHROPIC_API_KEY

6. **DeepSeek-R1** - 94.3% (Open-Source!)
   - **OpenRouter**: `deepseek/deepseek-r1`
   - **Direct API**: DEEPSEEK_API_KEY
   - **License**: MIT

7. **Gemini 2.5 Pro** - 92%+ (estimated)
   - **OpenRouter**: `google/gemini-2.5-pro`
   - **Direct API**: GEMINI_API_KEY

8. **Claude Sonnet 4.5** - 90%+ (estimated)
   - **OpenRouter**: `anthropic/claude-sonnet-4.5`
   - **Direct API**: ANTHROPIC_API_KEY

9. **Qwen3-Math** - 88%+ (estimated)
   - **OpenRouter**: `qwen/qwen3-math`
   - **Ollama**: `qwen2.5-math:72b`

10. **Llama 3.3 70B** - 85%+ (estimated)
    - **OpenRouter**: `meta-llama/llama-3.3-70b-instruct`
    - **Ollama**: `llama3.3:70b`

---

### 🔬 **SCIENCE** (MMLU, GPQA)

**Benchmark**: Graduate-level scientific knowledge  
**Source**: Multiple benchmarks (MMLU, MMLU-Pro, GPQA)  
**Metric**: Comprehensive scientific understanding

**Top 10 Models:**

1. **GPT-5.1** - State-of-the-art
   - ALL access methods available

2. **Grok 4** - 87.5% GPQA
   - **OpenRouter**: `x-ai/grok-4`
   - **Direct API**: X_AI_API_KEY

3. **Gemini 2.5 Pro** - Excellent science
   - ALL access methods available

4. **Claude Sonnet 4.5** - Strong scientific reasoning
   - ALL access methods available

5. **OpenAI o3** - Deep research capability
   - **OpenRouter**: `openai/o3`
   - **Direct API**: OPENAI_API_KEY

6. **Claude Opus 4.1** - Maximum scientific capability
   - **OpenRouter**: `anthropic/claude-opus-4.1`
   - **Direct API**: ANTHROPIC_API_KEY

7. **DeepSeek-R1** - Open-source scientific reasoning
   - **OpenRouter**: `deepseek/deepseek-r1`
   - **Direct API**: DEEPSEEK_API_KEY

8. **Qwen3-235B** - Large-scale scientific reasoning
   - **OpenRouter**: `qwen/qwen3-vl-235b-a22b-thinking`

9. **Llama 3.3 70B** - Good scientific knowledge
   - **OpenRouter**: `meta-llama/llama-3.3-70b-instruct`
   - **Ollama**: `llama3.3:70b`

10. **Mistral Large 3** - Strong scientific reasoning
    - **OpenRouter**: `mistralai/mistral-large-3`
    - **Direct API**: MISTRAL_API_KEY

---

### 👁️ **VISION** (Image Understanding)

**Benchmark**: Various vision benchmarks  
**Metric**: Image analysis, OCR, document understanding

**Top 10 Models:**

1. **Gemini 2.5 Pro** - Best Vision
   - **OpenRouter**: `google/gemini-2.5-pro`
   - **Direct API**: GEMINI_API_KEY
   - **Features**: Native multimodal, video support

2. **Claude Sonnet 4.5** - Excellent Vision
   - **OpenRouter**: `anthropic/claude-sonnet-4.5`
   - **Direct API**: ANTHROPIC_API_KEY
   - **Best for**: Charts, graphs, documents

3. **GPT-5.1** - Strong Vision
   - **OpenRouter**: `openai/gpt-5.1`
   - **Direct API**: OPENAI_API_KEY

4. **Claude Opus 4.1** - Maximum Vision Capability
   - **OpenRouter**: `anthropic/claude-opus-4.1`
   - **Direct API**: ANTHROPIC_API_KEY

5. **Qwen3-VL-32B** - Open-Source Vision Specialist
   - **OpenRouter**: `qwen/qwen3-vl-32b-instruct`
   - **Features**: 32 languages OCR, document parsing

6. **Qwen3-VL-235B** - Large-Scale Vision
   - **OpenRouter**: `qwen/qwen3-vl-235b-a22b-thinking`
   - **Features**: Long-horizon video, temporal reasoning

7. **GPT-4o** - Previous Gen Vision (still good)
   - **OpenRouter**: `openai/gpt-4o`
   - **Direct API**: OPENAI_API_KEY

8. **Claude Haiku 4.5** - Fast Vision
   - **OpenRouter**: `anthropic/claude-haiku-4.5`
   - **Direct API**: ANTHROPIC_API_KEY

9. **Gemini 2.5 Flash** - Fast Multimodal
   - **OpenRouter**: `google/gemini-2.5-flash`
   - **Direct API**: GEMINI_API_KEY

10. **NVIDIA Nemotron Nano 2 VL** - Open-Source OCR
    - **OpenRouter**: `nvidia/nemotron-nano-2-vl`
    - **Features**: OCR-focused, lightweight

---

### 🎨 **IMAGE GENERATION**

**RECOMMENDATION**: Use Gemini 2.5 Flash Image for 90% of requests  
**Reason**: Ultra-cheap, excellent quality, contextual understanding

**Top 5 Models:**

1. **Gemini 2.5 Flash Image** ("Nano Banana") - **USE THIS FOR 90% OF IMAGES**
   - **OpenRouter**: `google/gemini-2.5-flash-image`
   - **Direct API**: GEMINI_API_KEY
   - **Cost**: $0.3/$2.5 per 1M tokens (ULTRA-CHEAP)
   - **Features**: Contextual understanding, multi-turn, edits

2. **GPT-5 Image** - Premium Quality
   - **OpenRouter**: `openai/gpt-5-image`
   - **Direct API**: OPENAI_API_KEY
   - **Cost**: $10/$10 per 1M tokens
   - **Features**: Superior instruction following, text rendering

3. **GPT-5 Image Mini** - Budget Premium
   - **OpenRouter**: `openai/gpt-5-image-mini`
   - **Direct API**: OPENAI_API_KEY
   - **Cost**: $2.5/$2 per 1M tokens

4. **DALL-E 3** - Legacy (not recommended)
   - **OpenRouter**: `openai/dall-e-3`
   - **Direct API**: OPENAI_API_KEY
   - **Reason**: Use Gemini instead (better & cheaper)

5. **Stable Diffusion XL** - Open-Source
   - **Ollama**: Various SDXL models
   - **Local**: Free, privacy-preserving

---

### 🔊 **AUDIO** (Speech & Understanding)

**Top 5 Models:**

1. **Mistral Voxtral Small 24B** - State-of-the-Art Audio
   - **OpenRouter**: `mistralai/voxtral-small-24b-2507`
   - **Cost**: $100 per million seconds of audio
   - **Features**: Transcription, translation, understanding

2. **Gemini 2.5 Pro** - Native Audio
   - **OpenRouter**: `google/gemini-2.5-pro`
   - **Direct API**: GEMINI_API_KEY
   - **Features**: Text, audio, video, images (native multimodal)

3. **GPT-4o Audio** - Audio Input Support
   - **OpenRouter**: `openai/gpt-4o-audio-preview`
   - **Direct API**: OPENAI_API_KEY
   - **Features**: Audio input detection, nuanced understanding

4. **Whisper Large V3** - Open-Source Transcription
   - **Ollama**: Various Whisper models
   - **Features**: Multi-language transcription

5. **Gemini 2.5 Flash** - Fast Audio
   - **OpenRouter**: `google/gemini-2.5-flash`
   - **Direct API**: GEMINI_API_KEY

---

### 🎬 **VIDEO** (Video Understanding)

**Top 5 Models:**

1. **Qwen3-VL-235B** - Best Video Understanding
   - **OpenRouter**: `qwen/qwen3-vl-235b-a22b-thinking`
   - **Features**: Long-horizon video, temporal reasoning

2. **Gemini 2.5 Pro** - Native Video Support
   - **OpenRouter**: `google/gemini-2.5-pro`
   - **Direct API**: GEMINI_API_KEY
   - **Features**: Video-to-code, affective dialogue

3. **Qwen3-VL-32B** - Efficient Video
   - **OpenRouter**: `qwen/qwen3-vl-32b-instruct`
   - **Features**: Timeline alignment, GUI automation

4. **GPT-5.1** - Video Capabilities
   - **OpenRouter**: `openai/gpt-5.1`
   - **Direct API**: OPENAI_API_KEY

5. **Claude Sonnet 4.5** - Video Analysis
   - **OpenRouter**: `anthropic/claude-sonnet-4.5`
   - **Direct API**: ANTHROPIC_API_KEY

---

### 🤖 **AGENTIC TASKS** (OSWorld, Computer Use)

**Benchmark**: OSWorld computer use benchmark  
**Metric**: Autonomous task completion

**Top 10 Models:**

1. **Claude Sonnet 4.5** - 61.4% | **Best Agentic**
   - ALL access methods available
   - **Best for**: Extended autonomous operation

2. **GPT-5.1-Codex** - Agentic Coding Specialist
   - **OpenRouter**: `openai/gpt-5.1-codex`
   - **Direct API**: OPENAI_API_KEY
   - **Features**: Multi-hour runs, structured reviews

3. **Claude Opus 4.1** - Maximum Agentic Capability
   - **OpenRouter**: `anthropic/claude-opus-4.1`
   - **Direct API**: ANTHROPIC_API_KEY

4. **Claude Haiku 4.5** - Fast Agentic
   - **OpenRouter**: `anthropic/claude-haiku-4.5`
   - **Direct API**: ANTHROPIC_API_KEY

5. **GPT-5.1** - Strong Agentic
   - ALL access methods available

6. **Gemini 2.5 Pro** - Native Agentic
   - ALL access methods available

7. **Qwen3-Coder** - Open-Source Agentic
   - **OpenRouter**: `qwen/qwen3-coder`

8. **Devstral Medium** - Cost-Effective Agentic
   - **OpenRouter**: `mistralai/devstral-medium`

9. **DeepSeek-R1** - Open-Source Reasoning Agent
   - **OpenRouter**: `deepseek/deepseek-r1`
   - **Direct API**: DEEPSEEK_API_KEY

10. **Llama 3.1 405B** - Best Open-Source Function Calling (81.1% BFCL)
    - **OpenRouter**: `meta-llama/llama-3.1-405b-instruct`

---

### ⚡ **SPEED** (Tokens/Second)

**Top 10 Fastest Models:**

1. **Llama 4 Scout** - 2600 t/s
   - **OpenRouter**: `meta-llama/llama-4-scout`
   - **Ollama**: `llama4-scout`

2. **Llama 3.3 70B** - 2500 t/s
   - **OpenRouter**: `meta-llama/llama-3.3-70b-instruct`
   - **Ollama**: `llama3.3:70b`

3. **Llama 3.1 70B** - 2100 t/s
   - **OpenRouter**: `meta-llama/llama-3.1-70b-instruct`
   - **Ollama**: `llama3.1:70b`

4. **Llama 3.1 8B** - 1800 t/s
   - **OpenRouter**: `meta-llama/llama-3.1-8b-instruct`
   - **Ollama**: `llama3.1:8b`

5. **Gemini 2.5 Flash** - ~200 t/s
   - **OpenRouter**: `google/gemini-2.5-flash`
   - **Direct API**: GEMINI_API_KEY

6. **Gemini 2.5 Flash Lite** - Ultra-fast
   - **OpenRouter**: `google/gemini-2.5-flash-lite`
   - **Direct API**: GEMINI_API_KEY

7. **Grok Code Fast 1** - 92 t/s (excellent coding!)
   - **OpenRouter**: `x-ai/grok-code-fast-1`
   - **Direct API**: X_AI_API_KEY

8. **Claude Haiku 4.5** - ~51 t/s (near-frontier quality)
   - **OpenRouter**: `anthropic/claude-haiku-4.5`
   - **Direct API**: ANTHROPIC_API_KEY

9. **Mistral Small 3.2** - Very fast
   - **OpenRouter**: `mistralai/mistral-small-3.2-24b-instruct`
   - **Direct API**: MISTRAL_API_KEY

10. **Phi-4 14B** - Lightweight & Fast
    - **OpenRouter**: `microsoft/phi-4`
    - **Ollama**: `phi4:14b`

---

### 💰 **COST EFFICIENCY** (Price/Performance)

**Top 10 Most Cost-Effective:**

1. **Gemini 2.5 Flash** - Best Overall Value
   - **Cost**: $0.0003/$0.0025 per 1M tokens
   - **OpenRouter**: `google/gemini-2.5-flash`
   - **Direct API**: GEMINI_API_KEY

2. **Gemini 2.5 Flash Lite** - Ultra-Cheap
   - **Cost**: $0.0001/$0.0004 per 1M tokens
   - **OpenRouter**: `google/gemini-2.5-flash-lite`
   - **Direct API**: GEMINI_API_KEY

3. **DeepSeek V3.1 Terminus** - Open-Source Value
   - **Cost**: $0.00023/$0.0009 per 1M tokens
   - **OpenRouter**: `deepseek/deepseek-v3.1-terminus`
   - **Direct API**: DEEPSEEK_API_KEY

4. **Mistral Small 3.2 24B** - Very Affordable
   - **Cost**: $0.00006/$0.00018 per 1M tokens
   - **OpenRouter**: `mistralai/mistral-small-3.2-24b-instruct`
   - **Direct API**: MISTRAL_API_KEY

5. **Gemini 2.5 Flash Image** - Cheapest Images
   - **Cost**: $0.0003/$0.0025 per 1M tokens
   - **OpenRouter**: `google/gemini-2.5-flash-image`
   - **Direct API**: GEMINI_API_KEY

6. **Nova Micro** - Ultra Budget
   - **Cost**: $0.04/$0.14 per 1M tokens
   - **OpenRouter**: `cohere/nova-micro`

7. **Gemma 3 27B** - Free & Open
   - **Cost**: $0.07/$0.07 per 1M tokens
   - **OpenRouter**: `google/gemma-3-27b-it`
   - **Ollama**: `gemma2:27b`

8. **Llama 3.3 70B** - Free via Ollama
   - **OpenRouter**: Paid
   - **Ollama**: FREE (local)

9. **Qwen2.5 72B** - Free via Ollama
   - **OpenRouter**: Paid
   - **Ollama**: FREE (local)

10. **DeepSeek-Coder-V2** - Free via Ollama
    - **OpenRouter**: Paid
    - **Ollama**: FREE (local)
    - **License**: MIT

---

## Minimum Model Requirements (ENFORCED)

### For Peer-Based Work (Coding, Testing, Review)

**MINIMUM ACCEPTABLE MODELS:**

| Provider | Minimum Version | Recommended | OpenRouter ID | Direct API |
|----------|----------------|-------------|---------------|------------|
| **OpenAI** | GPT-5 | GPT-5.1-Codex | `openai/gpt-5.1-codex` | OPENAI_API_KEY |
| **Google** | Gemini 2.5 Flash | Gemini 2.5 Pro | `google/gemini-2.5-pro` | GEMINI_API_KEY |
| **Anthropic** | Claude 4.5 Haiku | Claude 4.5 Sonnet | `anthropic/claude-sonnet-4.5` | ANTHROPIC_API_KEY |
| **xAI** | Grok 3 | Grok 4 | `x-ai/grok-4` | X_AI_API_KEY |
| **DeepSeek** | DeepSeek V3 | DeepSeek V3.1 Terminus | `deepseek/deepseek-v3.1-terminus` | DEEPSEEK_API_KEY |

**FORBIDDEN (All Providers):**
- ❌ GPT-4, GPT-4o, GPT-4-turbo (use GPT-5+)
- ❌ Claude 3.x (use Claude 4.5+)
- ❌ Gemini 1.x (use Gemini 2.5+)
- ❌ Grok 2.x (use Grok 3+)
- ❌ DeepSeek V2 (use V3+)

### Enforcement in Startup

Startup script (`startup.ps1`) MUST:
1. Load this file (Universal-Model-Registry.md)
2. Display ALL access methods (Direct API, OpenRouter, Ollama)
3. Show which API keys are configured
4. Validate minimum model levels for peer work
5. Warn if using outdated models

---

## Quick Selection Guide

### By Task & Access Method

**Coding Task:**
- **Direct API**: OpenAI GPT-5.1-Codex (OPENAI_API_KEY)
- **OpenRouter**: `openai/gpt-5.1-codex` or `anthropic/claude-sonnet-4.5`
- **Ollama**: `qwen2.5-coder:32b` or `deepseek-coder-v2:236b`

**Reasoning Task:**
- **Direct API**: Gemini 2.5 Pro (GEMINI_API_KEY)
- **OpenRouter**: `google/gemini-2.5-pro` or `x-ai/grok-4`
- **Ollama**: `llama3.3:70b` or `qwen2.5:72b`

**Vision Task:**
- **Direct API**: Gemini 2.5 Pro (GEMINI_API_KEY)
- **OpenRouter**: `google/gemini-2.5-pro`
- **No Ollama Option**: Use cloud models

**Image Generation:**
- **Direct API**: Gemini 2.5 Flash Image (GEMINI_API_KEY)
- **OpenRouter**: `google/gemini-2.5-flash-image` ← **USE THIS**
- **Ollama**: Stable Diffusion models

**Fast/Cheap Task:**
- **Direct API**: Gemini 2.5 Flash (GEMINI_API_KEY)
- **OpenRouter**: `google/gemini-2.5-flash-lite`
- **Ollama**: `llama3.1:8b` or `phi4:14b`

---

## Related Documentation

- **OpenRouter Guide**: `C:\Users\kento\.cursor\global-cursor-repo\docs\OpenRouter-AI-MCP-Complete-Guide.md`
- **Update Command**: `C:\Users\kento\.cursor\commands\update-models.md`
- **Minimum Levels**: `C:\Users\kento\.cursor\global-cursor-repo\workflows\minimum-model-levels.md` (should point here)

---

## Update History

- **2025-11-19**: Complete consolidation - ALL access methods documented
- **2025-11-13**: Updated to GPT-5.1 series, Claude 4.5, Gemini 2.5
- **2025-11-05**: Initial Universal-Model-Rankings.md creation

---

**Version**: 2.0  
**Status**: ✅ ACTIVE - Single Source of Truth  
**Authority**: ALL model references must point here  
**Location**: `C:\Users\kento\.cursor\global-cursor-repo\docs\Universal-Model-Registry.md`


