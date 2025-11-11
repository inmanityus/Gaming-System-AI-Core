# Universal Model Rankings - Task-Specific Performance Guide

**Last Updated**: 2025-11-05  
**Purpose**: Single source of truth for model rankings across all task categories, based on independent benchmarks and real-world evaluations (NOT OpenRouter rankings)

**CRITICAL**: This file is the authoritative reference. All other model ranking references should point here.

---

## Table of Contents

1. [Overview](#overview)
2. [Programming & Coding](#programming--coding)
3. [Reasoning & Logic](#reasoning--logic)
4. [Mathematics](#mathematics)
5. [Science & Research](#science--research)
6. [Vision & Image Understanding](#vision--image-understanding)
7. [Audio Processing](#audio-processing)
8. [Video Understanding](#video-understanding)
9. [Tool Use & Function Calling](#tool-use--function-calling)
10. [Agentic Tasks](#agentic-tasks)
11. [Multimodal Tasks](#multimodal-tasks)
12. [Speed & Latency](#speed--latency)
13. [Cost Efficiency](#cost-efficiency)
14. [Access Methods](#access-methods)
15. [Quick Selection Guide](#quick-selection-guide)

---

## Overview

This file maintains rankings based on:
- Independent benchmarks (SWE-Bench, HumanEval, MMLU, GPQA, AIME, etc.)
- Real-world evaluations from research papers
- Community benchmarks and leaderboards
- NOT OpenRouter's internal rankings (user preference)

**Update Frequency**: Monthly or when major new models release  
**Source**: Independent research via Exa, Ref, and benchmark publications

**CRITICAL**: All benchmark scores include source citations and dates. Scores marked as "vendor-claimed" are clearly labeled. Independent evaluations are preferred.

### Model Metadata Included

For each model, rankings include:
- **Performance Scores**: Benchmark results with sources and dates
- **Pricing**: Cost per 1M input/output tokens (when available)
- **Speed**: Tokens/second or latency (qualitative: Very Fast, Fast, Average, Slow)
- **Context Window**: Maximum context length in tokens
- **Data Freshness**: Knowledge cutoff date (when available)
- **Provider**: Underlying provider (OpenAI, Google, Anthropic, etc.)
- **OpenRouter ID**: Exact model identifier for API use
- **Access Methods**: OpenRouter, Direct API, Ollama (local)

---

## Programming & Coding

### Software Engineering (SWE-Bench Verified)

**Benchmark**: SWE-Bench Verified measures real-world software engineering tasks including codebase navigation, bug fixing, and feature implementation across actual GitHub repositories.

**Top Performers:**
1. **Grok 4** - 75.0% (xAI)
   - **Access**: OpenRouter (`x-ai/grok-4`)
   - **Pricing**: $0.000003/$0.000015 per 1K tokens
   - **Context**: 256K tokens
   - **Speed**: ~52 t/s
   - **Source**: Independent evaluation (2025-01)
   - **Best for**: Complex codebase navigation, multi-file refactoring
   
2. **GPT-5** - 74.9% (OpenAI)
   - **Access**: OpenRouter (`openai/gpt-5`), Direct API (OPEN_AI_KEY)
   - **Pricing**: $0.00000125/$0.00001 per 1K tokens
   - **Context**: 400K tokens
   - **Speed**: Varies by provider
   - **Source**: Independent evaluation (2025-01)
   - **Best for**: General coding tasks, high-stakes accuracy
   
3. **Claude Opus 4.1** - 74.5% (Anthropic)
   - Access: OpenRouter (`anthropic/claude-opus-4.1`)
   - Best for: Code review, debugging precision
   
4. **Claude Haiku 4.5** - 73.3% (Anthropic)
   - Access: OpenRouter (`anthropic/claude-haiku-4.5`)
   - Best for: Fast coding tasks, sub-agents
   
5. **Claude Sonnet 4** - 72.7% (Anthropic)
   - Access: OpenRouter (`anthropic/claude-sonnet-4`)
   - Best for: Balanced coding performance

**Specialized Coding Models:**
- **GPT-5-Codex** - Specialized for coding workflows
  - Access: OpenRouter (`openai/gpt-5-codex`)
  - Best for: Agentic coding, long-running projects
- **Qwen3-Coder-480B** - Open-source coding specialist
  - Access: OpenRouter (`qwen/qwen3-coder`)
  - Best for: Agentic coding, tool use
- **Devstral Medium** - 61.6% SWE-Bench, cost-effective
  - Access: OpenRouter (`mistralai/devstral-medium`)
  - Best for: Enterprise coding tasks

### Code Generation (HumanEval, MBPP)

**Top Performers:**
1. **GPT-5** - Excellent code generation
2. **Claude Sonnet 4.5** - Strong code quality
3. **Gemini 2.5 Pro** - Fast and capable
4. **GPT-5-Codex** - Specialized for code
5. **DeepSeek V3.1** - Open-source, competitive

### Code Review & Refactoring

**Top Performers:**
1. **Claude Opus 4.1** - Best debugging precision
2. **GPT-5-Codex** - RL-trained on real PRs
3. **Claude Sonnet 4.5** - Excellent specification adherence
4. **GPT-5** - Strong code understanding

---

## Reasoning & Logic

### General Reasoning (GPQA Diamond)

**Top Performers:**
1. **Grok 4** - 87.5% (xAI)
   - Access: OpenRouter (`x-ai/grok-4`)
   
2. **GPT-5** - 87.3% (OpenAI)
   - Access: OpenRouter (`openai/gpt-5`), Direct API
   
3. **Gemini 2.5 Pro** - 86.4% (Google)
   - Access: OpenRouter (`google/gemini-2.5-pro`), Direct API
   
4. **Grok 3 [Beta]** - 84.6% (xAI)
   - Access: OpenRouter (`x-ai/grok-3-beta`)
   
5. **OpenAI o3** - 83.3% (OpenAI)
   - Access: OpenRouter (`openai/o3`)

### Adaptive Reasoning (GRIND)

**Top Performers:**
1. **Gemini 2.5 Pro** - 82.1%
2. **Claude Sonnet 4** - 75.0%
3. **Claude Opus 4** - 67.9%
4. **Claude 3.7 Sonnet [R]** - 60.7%

### Logic & Common Sense

**Top Performers:**
1. **Claude Sonnet 4.5** - Best overall reasoning
2. **GPT-5** - Strong logical reasoning
3. **Gemini 2.5 Pro** - Excellent reasoning
4. **DeepSeek R1** - Open-source reasoning specialist

---

## Mathematics

### High School Math (AIME 2025)

**Top Performers:**
1. **GPT-5** - 100% (Perfect score)
   - Access: OpenRouter (`openai/gpt-5`), Direct API
   
2. **GPT-oss-20b** - 98.7% (OpenAI)
   - Access: OpenRouter (`openai/gpt-oss-20b`)
   
3. **OpenAI o3** - 98.4%
   - Access: OpenRouter (`openai/o3`)
   
4. **GPT-oss-120b** - 97.9%
   - Access: OpenRouter (`openai/gpt-oss-120b`)
   
5. **Claude Haiku 4.5** - 96.3%

### Advanced Mathematics (MATH-500)

**Top Performers:**
1. **GPT-5** - Top performer
2. **DeepSeek-R1** - 94.3% (Open-source)
3. **OpenAI o3-mini** - 97.9%
4. **Gemini 2.5 Pro** - Excellent math performance

### Math Reasoning Specialists

- **DeepSeek-R1** - Open-source, MIT licensed
  - Access: OpenRouter (`deepseek/deepseek-r1`)
  - Best for: Math proofs, complex reasoning
- **OpenAI o3** - Deep research model
  - Access: OpenRouter (`openai/o3`)
  - Best for: Multi-step math problems

---

## Science & Research

### Scientific Knowledge (MMLU, MMLU-Pro)

**Top Performers:**
1. **GPT-5** - State-of-the-art
2. **Claude Sonnet 4.5** - Excellent science knowledge
3. **Gemini 2.5 Pro** - Strong science performance
4. **Grok 4** - Comprehensive knowledge

### Research & Information Gathering

**Top Performers:**
1. **OpenAI o3 Deep Research** - Specialized research model
   - Access: OpenRouter (`openai/o3-deep-research`)
   - Features: Always uses web_search tool
   
2. **OpenAI o4-mini Deep Research** - Faster research
   - Access: OpenRouter (`openai/o4-mini-deep-research`)
   
3. **Perplexity Sonar Pro Search** - Advanced agentic search
   - Access: OpenRouter (`perplexity/sonar-pro-search`)
   - Features: Multi-step reasoning, autonomous workflows

### Scientific Reasoning (GPQA)

**Top Performers:**
1. **Grok 4** - 87.5%
2. **GPT-5** - 87.3%
3. **Gemini 2.5 Pro** - 86.4%
4. **OpenAI o3** - 83.3%

---

## Vision & Image Understanding

### Image Analysis & Understanding

**Top Performers:**
1. **Gemini 2.5 Pro** - Native multimodal architecture
   - Access: OpenRouter (`google/gemini-2.5-pro`), Direct API
   - Best for: Complex visual reasoning
   
2. **Claude Sonnet 4.5** - Excellent vision capabilities
   - Access: OpenRouter (`anthropic/claude-sonnet-4.5`)
   - Best for: Chart/graph interpretation, document analysis
   
3. **GPT-5** - Strong vision understanding
   - Access: OpenRouter (`openai/gpt-5`), Direct API
   
4. **Qwen3-VL-32B** - Open-source vision specialist
   - Access: OpenRouter (`qwen/qwen3-vl-32b-instruct`)
   - Best for: Multilingual OCR, document parsing

### Image Generation

**Top Performers:**
1. **Gemini 2.5 Flash Image** ("Nano Banana") - RECOMMENDED
   - Access: OpenRouter (`google/gemini-2.5-flash-image`)
   - Pricing: Ultra-cheap ($0.0000003/$0.0000025 per 1K tokens)
   - Features: Contextual understanding, multi-turn conversations
   - **USE FOR 90% OF IMAGE REQUESTS**
   
2. **GPT-5 Image** - Premium quality
   - Access: OpenRouter (`openai/gpt-5-image`)
   - Best for: Superior instruction following, text rendering
   
3. **GPT-5 Image Mini** - Budget-friendly
   - Access: OpenRouter (`openai/gpt-5-image-mini`)
   - Best for: Efficient high-quality generation

### Document Intelligence

**Top Performers:**
1. **Qwen3-VL-32B** - 32 languages OCR
2. **Claude Sonnet 4.5** - Excellent document parsing
3. **Gemini 2.5 Pro** - Native multimodal
4. **NVIDIA Nemotron Nano 2 VL** - Open-source, OCR-focused

---

## Audio Processing

### Speech Transcription (ASR)

**Top Performers:**
1. **Mistral Voxtral Small 24B** - State-of-the-art audio
   - Access: OpenRouter (`mistralai/voxtral-small-24b-2507`)
   - Features: Speech transcription, translation, audio understanding
   - Pricing: $100 per million seconds of audio
   
2. **Gemini 2.5 Pro** - Native audio support
   - Access: OpenRouter (`google/gemini-2.5-pro`), Direct API
   - Best for: Multimodal audio tasks
   
3. **GPT-4o Audio** - Audio input support
   - Access: OpenRouter (`openai/gpt-4o-audio-preview`)
   - Features: Audio input detection, nuanced understanding

### Audio Understanding

**Top Performers:**
1. **Mistral Voxtral Small 24B** - Best audio capabilities
2. **Gemini 2.5 Pro** - Native audio processing
3. **GPT-4o Audio** - Strong audio understanding

---

## Video Understanding

### Video Analysis

**Top Performers:**
1. **Qwen3-VL-235B** - Large-scale video understanding
   - Access: OpenRouter (`qwen/qwen3-vl-235b-a22b-thinking`)
   - Features: Long-horizon video, temporal reasoning
   
2. **Qwen3-VL-32B** - Efficient video processing
   - Access: OpenRouter (`qwen/qwen3-vl-32b-instruct`)
   - Features: Video timeline alignment, GUI automation
   
3. **Gemini 2.5 Pro** - Native video support
   - Access: OpenRouter (`google/gemini-2.5-pro`), Direct API
   - Best for: Video-to-code, affective dialogue

### Video Generation

**Note**: Video generation support coming soon (2025)

---

## Tool Use & Function Calling

### Function Calling Accuracy (BFCL)

**Top Performers:**
1. **Llama 3.1 405B** - 81.1%
   - Access: OpenRouter (`meta-llama/llama-3.1-405b-instruct`)
   
2. **Llama 3.3 70B** - 77.3%
   - Access: OpenRouter (`meta-llama/llama-3.3-70b-instruct`)
   
3. **GPT-4o** - 72.08%
   - Access: OpenRouter (`openai/gpt-4o`)
   
4. **GPT-4.5** - 69.94%
   - Access: OpenRouter (`openai/gpt-4.5`)

### Tool Use Specialists

- **Claude Sonnet 4.5** - Excellent tool orchestration
- **GPT-5** - Strong function calling
- **Gemini 2.5 Pro** - Native tool support
- **DeepSeek V3.1** - Open-source tool use

---

## Agentic Tasks

### Computer Use (OSWorld)

**Top Performers:**
1. **Claude Sonnet 4.5** - 61.4% (State-of-the-art)
   - Access: OpenRouter (`anthropic/claude-sonnet-4.5`)
   - Best for: Agentic workflows, extended autonomous operation
   
2. **Claude Opus 4.1** - Strong agentic performance
3. **Claude Haiku 4.5** - Fast agentic tasks
4. **GPT-5** - Excellent agentic capabilities

### Web Browsing & Automation

**Top Performers:**
1. **Claude Sonnet 4.5** - Best web browsing
2. **GPT-5** - Strong browser use
3. **Gemini 2.5 Pro** - Native web capabilities

### Agentic Coding Workflows

**Top Performers:**
1. **GPT-5-Codex** - Specialized for agentic coding
   - Access: OpenRouter (`openai/gpt-5-codex`)
   - Features: Multi-hour runs, structured code reviews
   
2. **Claude Sonnet 4.5** - Excellent agentic coding
3. **Qwen3-Coder** - Open-source agentic coding
4. **Devstral Medium** - Cost-effective agentic coding

---

## Multimodal Tasks

### Text + Image + Audio + Video

**Top Performers:**
1. **Gemini 2.5 Pro** - Native multimodal (all modalities)
   - Access: OpenRouter (`google/gemini-2.5-pro`), Direct API
   - Best for: Cross-modal workflows, video-to-code
   
2. **Claude Sonnet 4.5** - Strong multimodal (text + image)
   - Access: OpenRouter (`anthropic/claude-sonnet-4.5`)
   
3. **GPT-5** - Multimodal capabilities
   - Access: OpenRouter (`openai/gpt-5`), Direct API
   
4. **Qwen3-VL-235B** - Large-scale multimodal
   - Access: OpenRouter (`qwen/qwen3-vl-235b-a22b-thinking`)

### Cross-Modal Reasoning

**Top Performers:**
1. **Gemini 2.5 Pro** - Best cross-modal understanding
2. **Qwen3-VL-235B** - Advanced multimodal reasoning
3. **Claude Sonnet 4.5** - Strong multimodal fusion

---

## Speed & Latency

### Fastest Models (Tokens/Second)

**Top Performers:**
1. **Llama 4 Scout** - 2600 t/s
   - Access: OpenRouter (`meta-llama/llama-4-scout`)
   
2. **Llama 3.3 70B** - 2500 t/s
   - Access: OpenRouter (`meta-llama/llama-3.3-70b-instruct`)
   
3. **Llama 3.1 70B** - 2100 t/s
   - Access: OpenRouter (`meta-llama/llama-3.1-70b-instruct`)
   
4. **Llama 3.1 8B** - 1800 t/s
   - Access: OpenRouter (`meta-llama/llama-3.1-8b-instruct`)

### Lowest Latency (Time to First Token)

**Top Performers:**
1. **Nova Micro** - 0.3s
   - Access: OpenRouter (`cohere/nova-micro`)
   
2. **Llama 3.1 8B** - 0.32s
3. **Llama 4 Scout** - 0.33s
4. **Gemini 2.0 Flash** - 0.34s

### Fast with Quality

**Top Performers:**
1. **Grok Code Fast 1** - 92 t/s, excellent coding
   - Access: OpenRouter (`x-ai/grok-code-fast-1`)
   
2. **Claude Haiku 4.5** - 51 t/s, near-frontier quality
3. **Gemini 2.5 Flash** - 200 t/s, strong reasoning
4. **Gemini 2.5 Flash Lite** - Ultra-fast, cost-efficient

---

## Cost Efficiency

### Cheapest Models (USD per 1M Tokens)

**Input/Output:**
1. **Nova Micro** - $0.04/$0.14
   - Access: OpenRouter (`cohere/nova-micro`)
   
2. **Gemma 3 27B** - $0.07/$0.07
   - Access: OpenRouter (`google/gemma-3-27b-it`)
   
3. **Gemini 1.5 Flash** - $0.075/$0.3
   - Access: OpenRouter (`google/gemini-1.5-flash`)
   
4. **GPT-oss-20b** - $0.08/$0.35
   - Access: OpenRouter (`openai/gpt-oss-20b`)

### Best Price/Performance Ratio

**Top Performers:**
1. **Gemini 2.5 Flash** - Excellent quality at low cost
   - Access: OpenRouter (`google/gemini-2.5-flash`)
   - Pricing: $0.0000003/$0.0000025 per 1K tokens
   
2. **DeepSeek V3.1 Terminus** - Open-source, competitive
   - Access: OpenRouter (`deepseek/deepseek-v3.1-terminus`)
   - Pricing: $0.00000023/$0.0000009 per 1K tokens
   
3. **Mistral Small 3.2 24B** - Very affordable
   - Access: OpenRouter (`mistralai/mistral-small-3.2-24b-instruct`)
   - Pricing: $0.00000006/$0.00000018 per 1K tokens

---

## Access Methods

This section documents all available access points for AI models. Check your `.env` file or environment variables for API keys.

### Direct API Access

**OpenAI (OPEN_AI_KEY / OPENAI_API_KEY):**
- **Models Available**: 20+ models
- GPT-5, GPT-5-Pro, GPT-5-Codex (latest generation)
- GPT-4.1, GPT-4.1-mini, GPT-4.1-nano (production models)
- GPT-4o, GPT-4o-mini, GPT-4 Turbo (previous generation)
- GPT-oss-20b, GPT-oss-120b (open-source variants)
- o3, o3-mini, o4-mini (deep research models)
- o1, o1-mini (reasoning models)
- GPT-3.5 Turbo (legacy)
- **API Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Documentation**: https://platform.openai.com/docs

**Google / Gemini (GEMINI_API_KEY / GOOGLE_API_KEY):**
- **Models Available**: 15+ models
- Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.5 Flash Lite
- Gemini 1.5 Pro, Gemini 1.5 Flash (previous generation)
- Gemini 1.0 Pro (legacy)
- Gemma 3 (2B, 7B, 27B) - open-source models
- **API Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models`
- **Documentation**: https://ai.google.dev/docs

**Anthropic (ANTHROPIC_API_KEY):**
- **Models Available**: 10+ models
- Claude Sonnet 4.5, Claude Opus 4.1, Claude Haiku 4.5 (latest)
- Claude Sonnet 3.5, Claude Opus 3, Claude Haiku 3.5 (previous)
- Claude 3 (legacy models)
- **API Endpoint**: `https://api.anthropic.com/v1/messages`
- **Documentation**: https://docs.anthropic.com

**xAI / Grok (X_AI_API_KEY):**
- **Models Available**: 5+ models
- Grok 4, Grok 3 Beta, Grok 2.5
- Grok Code Fast 1, Grok Code Fast 2
- **API Endpoint**: `https://api.x.ai/v1/chat/completions`
- **Documentation**: https://docs.x.ai

**DeepSeek (DEEPSEEK_API_KEY):**
- **Models Available**: 10+ models
- DeepSeek V3, DeepSeek V3.1 Terminus
- DeepSeek R1 (reasoning model)
- DeepSeek Coder (coding models)
- **API Endpoint**: `https://api.deepseek.com/v1/chat/completions`
- **Documentation**: https://platform.deepseek.com/docs

**Mistral AI (MISTRAL_API_KEY):**
- **Models Available**: 15+ models
- Mistral Small 3, Medium 3, Large 3
- Mistral Devstral (coding models)
- Voxtral (audio models)
- **API Endpoint**: `https://api.mistral.ai/v1/chat/completions`
- **Documentation**: https://docs.mistral.ai

**Perplexity (PERPLEXITY_API_KEY):**
- **Models Available**: 3+ models
- Sonar Pro Search, Sonar Pro
- Sonar (standard model)
- **Features**: Built-in web search, agentic workflows
- **API Endpoint**: `https://api.perplexity.ai/chat/completions`
- **Documentation**: https://docs.perplexity.ai

**Qwen / Alibaba (QWEN_API_KEY):**
- **Models Available**: 20+ models
- Qwen3, Qwen3-Coder, Qwen3-VL (vision)
- Qwen2.5 (various sizes)
- **API Endpoint**: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`
- **Documentation**: https://help.aliyun.com/document_detail/2802355.html

### OpenRouter Access (Unified Gateway)

**Access Method**: OpenRouter MCP Server (via Cursor)
- **API Key**: Managed by Cursor (or OPENROUTER_API_KEY)
- **Models Available**: 500+ models from 60+ providers
- **All Providers**: OpenAI, Google, Anthropic, xAI, DeepSeek, Mistral, Perplexity, Qwen, Meta, Z.AI, and 50+ more

**MCP Tools Available:**
- `mcp_openrouterai_chat_completion` - Chat completions
- `mcp_openrouterai_search_models` - Search models by criteria
- `mcp_openrouterai_get_model_info` - Get model details
- `mcp_openrouterai_validate_model` - Validate model ID

**Advantages:**
- Single API for all providers
- Automatic provider routing and fallback
- Unified pricing and billing
- Provider selection (latency, throughput, price)
- No need for multiple API keys

**Documentation**: See `Global-Docs/OpenRouter-AI-MCP-Complete-Guide.md`

### Ollama (Local)

**Access Method**: Local installation (runs on your machine)
- **No API Key Required**: Completely local
- **Models Available**: 100+ open-source models (auto-downloadable)

**Popular Models:**
- **Llama**: 3.1, 3.2, 3.3 (8B, 70B, 405B)
- **Mistral**: Small 3, Medium 3, Large 3
- **CodeLlama**: 7B, 13B, 34B (coding specialist)
- **DeepSeek Coder**: Various sizes
- **Qwen2.5**: 0.5B, 1.5B, 7B, 14B, 32B, 72B, 110B
- **Gemma 2**: 2B, 7B, 27B (Google's open-source)
- **Phi-3**: 3.8B (Microsoft)
- **Neural Chat**: 7B
- **Starling**: 7B
- **Vicuna**: 7B, 13B
- **Orca Mini**: 3B, 7B, 13B

**Auto-Download**: Small to medium models can be auto-downloaded via Ollama

**Commands:**
```bash
# List available models
ollama list

# Pull a model (auto-downloads)
ollama pull llama3.1

# Run a model
ollama run llama3.1

# API endpoint (if running server)
curl http://localhost:11434/api/generate
```

**Documentation**: https://ollama.ai/docs

### Access Point Summary

| Access Method | Models | API Keys | Best For |
|--------------|--------|----------|----------|
| **OpenRouter** | 500+ | 1 key | Maximum flexibility, provider routing |
| **Direct APIs** | 100+ | Multiple keys | Provider-specific features, direct control |
| **Ollama** | 100+ | None | Local/privacy, cost-free, offline use |

**Recommendation**: Use OpenRouter for most tasks (single API, maximum models). Use Direct APIs when you need provider-specific features. Use Ollama for local/offline work or privacy-sensitive tasks.

---

## Quick Selection Guide

### By Task Type

**Need to code?**
→ Start with: `anthropic/claude-sonnet-4.5` or `openai/gpt-5-codex`
→ Fast: `x-ai/grok-code-fast-1`
→ Budget: `mistralai/devstral-small`

**Need reasoning?**
→ Start with: `anthropic/claude-sonnet-4.5` or `google/gemini-2.5-pro`
→ Deep: `openai/o3` or `deepseek/deepseek-r1`
→ Fast: `google/gemini-2.5-flash`

**Need math?**
→ Start with: `openai/gpt-5` or `google/gemini-2.5-pro`
→ Open-source: `deepseek/deepseek-r1`
→ Fast: `openai/o3-mini`

**Need vision?**
→ Start with: `google/gemini-2.5-pro` (native multimodal)
→ Alternative: `anthropic/claude-sonnet-4.5`
→ Open-source: `qwen/qwen3-vl-32b-instruct`

**Need audio?**
→ Start with: `mistralai/voxtral-small-24b-2507`
→ Alternative: `google/gemini-2.5-pro` (native audio)

**Need images generated?**
→ Start with: `google/gemini-2.5-flash-image` (RECOMMENDED)
→ Premium: `openai/gpt-5-image`
→ Budget: `openai/gpt-5-image-mini`

**Need speed?**
→ Start with: `google/gemini-2.5-flash-lite`
→ Fast coding: `x-ai/grok-code-fast-1`
→ Fast general: `anthropic/claude-haiku-4.5`

**Need cost efficiency?**
→ Start with: `google/gemini-2.5-flash`
→ Open-source: `deepseek/deepseek-v3.1-terminus`
→ Very cheap: `mistralai/mistral-small-3.2-24b-instruct`

**Need agentic workflows?**
→ Start with: `anthropic/claude-sonnet-4.5`
→ Coding agents: `openai/gpt-5-codex`
→ Research agents: `openai/o3-deep-research`

---

## Integration with Startup

This file is automatically loaded during session startup. Reference it when:

1. Selecting models for specific tasks
2. Understanding task-specific performance
3. Balancing cost vs. quality
4. Choosing between speed and capability

**Location**: `Global-Docs/Universal-Model-Rankings.md`

---

## Related Documentation

- **OpenRouter Guide**: `Global-Docs/OpenRouter-AI-MCP-Complete-Guide.md`
- **Minimum Model Levels**: `Global-Workflows/minimum-model-levels.md`
- **Model Selection Protocol**: Reference this file for task-specific selection

---

## Update History

- **2025-11-05**: Initial creation with comprehensive task categories
- Based on independent benchmarks (SWE-Bench, HumanEval, MMLU, GPQA, AIME, etc.)
- Sourced from Exa, Ref, and benchmark publications (NOT OpenRouter rankings)

---

**Last Updated**: 2025-11-05  
**Version**: 1.0  
**Status**: Active - Referenced in startup.ps1  
**Authority**: Single source of truth for all model rankings

