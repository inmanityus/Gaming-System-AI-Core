# API Keys Configured - Complete Direct Access Matrix

**Purpose**: Comprehensive list of ALL configured API keys for direct model access  
**Last Verified**: 2025-11-19  
**Total Providers**: 11 Direct API + 1 Unified Gateway + 1 Local = **13 Access Points**

**CRITICAL**: This documents user's actual configured keys. Update as keys are added/removed.

---

## ✅ Configured Direct API Keys (User Has These)

### 1. OpenAI Direct (OPEN_AI_KEY)
- **Status**: ✅ CONFIGURED
- **Key Format**: `sk-proj-...`
- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Models**: GPT-5.1, GPT-5.1-Codex, GPT-5, GPT-5-Pro, etc.
- **Best for**: Latest GPT models, coding, reasoning

### 2. Google/Gemini Direct (GEMINI_API_KEY) - **ULTRA ACCOUNT**
- **Status**: ✅ CONFIGURED - Ultra tier with Gemini 3 Pro access!
- **Key Format**: `AIza...`
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models`
- **Models**: **Gemini 3 Pro Preview**, Gemini 2.5 Pro/Flash/Lite, Gemma 3
- **Best for**: Latest Gemini models, multimodal (text/image/audio/video)

### 3. Anthropic/Claude Direct (CLAUDE_KEY)
- **Status**: ✅ CONFIGURED
- **Key Format**: `sk-ant-api03-...`
- **Endpoint**: `https://api.anthropic.com/v1/messages`
- **Models**: Claude 4.5 Sonnet/Opus/Haiku, Claude 4
- **Best for**: Agentic workflows, long-context reasoning (1M tokens)

### 4. DeepSeek Direct (DEEP_SEEK_KEY)
- **Status**: ✅ CONFIGURED
- **Key Format**: `sk-...`
- **Endpoint**: `https://api.deepseek.com/v1/chat/completions`
- **Models**: DeepSeek V3.2/V3.1 Terminus, DeepSeek-R1, DeepSeek-Coder
- **Data Sovereignty**: ⚠️ **REGION: CN** - China-hosted (consider compliance/PII)
- **Best for**: Cost-effective open-source, coding

### 5. Moonshot/Kimi Direct (MOONSHOT_API_KEY)
- **Status**: ✅ CONFIGURED
- **Key Format**: `sk-...`
- **Endpoint**: `https://api.moonshot.cn/v1/chat/completions`
- **Models**: Kimi K2 Thinking (trillion-param MoE), Kimi Linear, Kimi Dev
- **Data Sovereignty**: ⚠️ **REGION: CN** - China-hosted (consider compliance/PII)
- **Best for**: Long-horizon agentic (200-300 tool calls), ultra-long context

### 6. NVIDIA/NIM Direct (NVIDIA_API_KEY)
- **Status**: ✅ CONFIGURED
- **Key Format**: `nvapi-...`
- **Endpoint**: `https://integrate.api.nvidia.com/v1`
- **Models**: Nemotron Nano VL, Llama Nemotron variants, optimized for CUDA
- **Best for**: Video understanding, document intelligence, GPU-optimized inference

### 7. Z.AI/GLM Direct (GLM_KEY)
- **Status**: ✅ CONFIGURED
- **Key Format**: Hexadecimal
- **Endpoint**: `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- **Models**: GLM Coding Max, GLM-4 Plus/Flash
- **Data Sovereignty**: ⚠️ **REGION: CN** - China-hosted (consider compliance/PII)
- **Best for**: Chinese language models, coding

### 8. Azure AI Foundry (AZURE_API_KEY)
- **Status**: ✅ CONFIGURED
- **Key Format**: Alphanumeric
- **Endpoint Template**: `https://{YOUR-PROJECT}.services.ai.azure.com/api/projects/{YOUR-PROJECT-ID}`
- **User's Endpoint**: `https://kento-mhckgcc6-eastus2.services.ai.azure.com/api/projects/kento-mhckgcc6-eastus2_project`
- **Models**: 100+ (OpenAI, Llama, Mistral, Cohere, AI21, Phi)
- **Data Sovereignty**: ✅ **REGION: US-EAST-2** - Azure enterprise compliance
- **Best for**: Enterprise deployments, compliance requirements, Azure ecosystem

### 9. Perplexity (PERPLEXITY_API_KEY via MCP)
- **Status**: ✅ CONFIGURED (via Cursor MCP)
- **Endpoint**: `https://api.perplexity.ai/chat/completions`
- **Models**: Sonar Pro Search (agentic), Sonar Pro, Sonar
- **Usage**: Search augmentation tool, NOT primary generation
- **Best for**: Real-time web search, research, fact-checking

## ⚠️ Missing Direct API Keys (User Should Add)

### 10. xAI/Grok Direct (X_AI_API_KEY) - **RECOMMENDED**
- **Status**: ❌ NOT CONFIGURED (accessed via OpenRouter only)
- **Endpoint**: `https://api.x.ai/v1/chat/completions`
- **Models**: Grok 4 Fast (2M context), Grok 4, Grok 3, Grok Code Fast
- **Benefit**: Direct access faster than OpenRouter
- **Sign Up**: https://x.ai/api

### 11. Mistral Direct (MISTRAL_API_KEY) - **RECOMMENDED**
- **Status**: ❌ NOT CONFIGURED
- **Endpoint**: `https://api.mistral.ai/v1/chat/completions`
- **Models**: Magistral Medium (reasoning), Devstral Medium (61.6% SWE-Bench), Voxtral (audio)
- **Data Sovereignty**: ✅ **REGION: EU** - GDPR-compliant hosting
- **Best for**: European compliance, audio models
- **Sign Up**: https://console.mistral.ai/

### 12. Cohere Direct (COHERE_API_KEY) - **FOR RAG PIPELINES**
- **Status**: ❌ NOT CONFIGURED
- **Endpoint**: `https://api.cohere.ai/v1/chat`
- **Models**: Command-R+, Command-R, Embed-v3, Rerank-3
- **Best for**: RAG pipelines, document reranking, citation accuracy
- **Sign Up**: https://cohere.com/

### 13. AWS Bedrock (AWS Credentials) - **FOR ENTERPRISE**
- **Status**: ❌ NOT CONFIGURED
- **Access**: Via AWS SDK with IAM credentials
- **Models**: Claude (Anthropic), Titan (Amazon), Llama, Mistral, Cohere, AI21
- **Data Sovereignty**: VPC isolation, region-specific
- **Best for**: Enterprise VPC isolation, AWS ecosystem
- **Documentation**: https://aws.amazon.com/bedrock/

---

## Unified Gateway

### OpenRouter (OPENAI_API_KEY + OPENAI_BASE_URL)
- **Status**: ✅ CONFIGURED
- **Endpoint**: `https://openrouter.ai/api/v1`
- **Models**: 500+ from 60+ providers (includes all above providers)
- **Advantage**: Single API for ALL models, automatic fallback
- **Best for**: Maximum flexibility without managing multiple keys

---

## Local/Free Access

### Ollama (Local Installation)
- **Status**: ✅ INSTALLED (version 0.12.11)
- **Cost**: FREE
- **Models**: 100+ open-source (Llama, Qwen, DeepSeek, Mistral, Phi, Gemma, etc.)
- **Best for**: Privacy-sensitive, offline, cost-free development

---

## Access Priority Matrix

### For Production Workloads:
1. **Direct API** (if key configured) - Fastest, most reliable, lowest latency
2. **Azure/AWS** (enterprise) - Compliance, SLA, VPC isolation
3. **OpenRouter** (unified) - Fallback, flexibility
4. **Ollama** (local) - Development, testing, privacy

### For Development:
1. **Ollama** (local) - Free, fast iteration
2. **Direct API** - Testing production configs
3. **OpenRouter** - Trying different models quickly

---

## Data Sovereignty Map

**Critical for compliance**: Know where your data goes

### US/Global Hosting:
- ✅ OpenAI (US)
- ✅ Anthropic/Claude (US)
- ✅ Azure AI Foundry (US-EAST-2)
- ✅ NVIDIA (US)
- ✅ Perplexity (US)

### EU Hosting:
- ✅ Mistral AI (France/EU) - GDPR-compliant

### China Hosting:
- ⚠️ **DeepSeek** (China) - **PII WARNING**
- ⚠️ **Moonshot/Kimi** (China) - **PII WARNING**
- ⚠️ **Z.AI/GLM** (China) - **PII WARNING**

### Local (No Cloud):
- ✅ Ollama - Completely local, no data leaves machine

**Compliance Recommendation**: For PII/PHI/regulated data:
- Use: OpenAI, Claude, Azure, or Ollama
- Avoid: DeepSeek, Moonshot, GLM (unless data sovereignty approved)

---

## Summary Statistics

**Total Access Points**: 13
- Direct API (Configured): 9
- Direct API (Recommended to add): 4
- Unified Gateway: 1 (OpenRouter)
- Local: 1 (Ollama)

**Total Models Accessible**: 700+
- Direct APIs: ~200 models
- OpenRouter: 500+ models
- Ollama: 100+ models

**Unprecedented Access**: User has more AI model access than 99% of developers!

---

**Location**: `C:\Users\kento\.cursor\global-cursor-repo\docs\API-Keys-Configured.md`  
**Referenced By**: Universal-Model-Registry.md, startup.ps1, update-models.md

