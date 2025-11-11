# OpenRouter AI MCP - Complete Guide

**Last Updated**: 2025-11-05  
**Purpose**: Comprehensive reference for all OpenRouter AI MCP capabilities, models, features, and tools available in Cursor sessions

---

## Table of Contents

1. [Overview](#overview)
2. [MCP Server Integration](#mcp-server-integration)
3. [Available Tools](#available-tools)
4. [Model Discovery](#model-discovery)
5. [Model Capabilities](#model-capabilities)
6. [API Features](#api-features)
7. [Provider Routing](#provider-routing)
8. [Multimodal Capabilities](#multimodal-capabilities)
9. [Tool Calling & Function Calling](#tool-calling--function-calling)
10. [Streaming](#streaming)
11. [Best Practices](#best-practices)
12. [Quick Reference](#quick-reference)

---

## Overview

OpenRouter AI MCP provides unified access to **500+ AI models** from **60+ providers** through a single, standardized API. This eliminates the need to manage multiple API keys and provides automatic failover, load balancing, and cost optimization.

### Key Benefits

- **Unified Interface**: One API for all models (OpenAI-compatible)
- **Automatic Failover**: Routes to best available provider automatically
- **Cost Optimization**: Selects best pricing across providers
- **Edge Performance**: ~25ms latency overhead
- **Higher Availability**: Distributed infrastructure with automatic fallback
- **Custom Data Policies**: Fine-grained control over data handling

### Statistics (2025)

- **20T+ Monthly Tokens** processed
- **4.2M+ Global Users**
- **60+ Active Providers**
- **500+ Models** available

---

## MCP Server Integration

### Access Method

OpenRouter AI MCP is available via the `mcp_openrouterai_*` tool family:

```typescript
// Search for models
mcp_openrouterai_search_models({
  query: "programming coding",
  provider: "openai",
  limit: 20
})

// Get model information
mcp_openrouterai_get_model_info({
  model: "anthropic/claude-sonnet-4.5"
})

// Chat completion
mcp_openrouterai_chat_completion({
  model: "google/gemini-2.5-pro",
  messages: [
    { role: "user", content: "Hello!" }
  ]
})

// Validate model
mcp_openrouterai_validate_model({
  model: "openai/gpt-5"
})
```

### Available Tools

1. **`mcp_openrouterai_chat_completion`** - Main chat completion API
2. **`mcp_openrouterai_search_models`** - Search and filter models
3. **`mcp_openrouterai_get_model_info`** - Get detailed model information
4. **`mcp_openrouterai_validate_model`** - Check if model ID is valid

---

## Model Discovery

### Search Models

Search for models by various criteria:

```typescript
// Search by query
mcp_openrouterai_search_models({
  query: "coding programming",
  limit: 50
})

// Filter by provider
mcp_openrouterai_search_models({
  provider: "anthropic",
  limit: 20
})

// Filter by capabilities
mcp_openrouterai_search_models({
  capabilities: {
    functions: true,
    vision: true
  }
})

// Filter by context length
mcp_openrouterai_search_models({
  minContextLength: 1000000,
  maxContextLength: 2000000
})

// Filter by pricing
mcp_openrouterai_search_models({
  maxPromptPrice: 0.001,
  maxCompletionPrice: 0.01
})
```

### Get Model Information

Get complete details about a specific model:

```typescript
mcp_openrouterai_get_model_info({
  model: "anthropic/claude-sonnet-4.5"
})
```

Returns:
- Model ID and canonical slug
- Name and description
- Context length
- Pricing (prompt, completion, request, image, web_search, etc.)
- Architecture (input/output modalities, tokenizer, instruct_type)
- Top provider details
- Supported parameters
- Capabilities (functions, tools, vision, json_mode)

### Validate Model

Quick check if a model ID exists:

```typescript
mcp_openrouterai_validate_model({
  model: "openai/gpt-5"
})
// Returns: true/false
```

---

## Model Capabilities

### Supported Parameters

Models support different parameters. Check `supported_parameters` array for each model:

- **`tools`** - Function calling capabilities
- **`tool_choice`** - Tool selection control
- **`max_tokens`** - Response length limiting
- **`temperature`** - Randomness control (0-2)
- **`top_p`** - Nucleus sampling (0-1)
- **`reasoning`** - Internal reasoning mode
- **`include_reasoning`** - Include reasoning in response
- **`structured_outputs`** - JSON schema enforcement
- **`response_format`** - Output format specification
- **`stop`** - Custom stop sequences
- **`frequency_penalty`** - Repetition reduction (-2 to 2)
- **`presence_penalty`** - Topic diversity (-2 to 2)
- **`seed`** - Deterministic outputs

### Architecture Features

Each model has an `architecture` object:

```typescript
{
  input_modalities: ["file", "image", "text"],  // Supported input types
  output_modalities: ["text"],                    // Supported output types
  tokenizer: "gpt-4",                           // Tokenization method
  instruct_type: "chat" | null                  // Instruction format
}
```

### Capabilities Flags

- **`functions`**: Supports function calling
- **`tools`**: Supports tool use
- **`vision`**: Supports image/video input
- **`json_mode`**: Supports guaranteed JSON output

---

## API Features

### Chat Completion

Standard OpenAI-compatible chat completion:

```typescript
mcp_openrouterai_chat_completion({
  model: "anthropic/claude-sonnet-4.5",
  messages: [
    { role: "system", content: "You are a helpful assistant." },
    { role: "user", content: "Explain quantum computing" }
  ],
  temperature: 0.7,
  max_tokens: 1000,
  stream: false
})
```

### Request Parameters

**Required:**
- `messages` OR `prompt` - Conversation messages or single prompt

**Optional:**
- `model` - Model ID (uses default if omitted)
- `stream` - Enable streaming (default: false)
- `max_tokens` - Max output tokens (1 to context_length)
- `temperature` - Randomness (0-2, default varies)
- `top_p` - Nucleus sampling (0-1)
- `stop` - Stop sequences (string or array)
- `seed` - Random seed for determinism
- `tools` - Function definitions for tool calling
- `tool_choice` - Tool selection mode
- `response_format` - Force JSON output (for supported models)

**OpenRouter-Specific:**
- `transforms` - Prompt transformations
- `models` - Model routing options
- `route` - Fallback routing strategy
- `provider` - Provider preferences (see Provider Routing)
- `user` - User identifier for abuse detection

### Response Format

```typescript
{
  id: "gen-xxxxxxxxxxxxxx",
  choices: [
    {
      finish_reason: "stop",
      native_finish_reason: "stop",
      message: {
        role: "assistant",
        content: "Response text",
        tool_calls?: ToolCall[]
      }
    }
  ],
  created: 1234567890,
  model: "anthropic/claude-sonnet-4.5",
  usage: {
    prompt_tokens: 100,
    completion_tokens: 200,
    total_tokens: 300
  }
}
```

### Finish Reasons

Normalized to: `tool_calls`, `stop`, `length`, `content_filter`, `error`

Raw finish reason available via `native_finish_reason` property.

---

## Provider Routing

Control how requests are routed to providers using the `provider` parameter:

```typescript
mcp_openrouterai_chat_completion({
  model: "anthropic/claude-sonnet-4.5",
  messages: [...],
  provider: {
    // Order providers to try
    order: ["anthropic", "openai"],
    
    // Allow fallbacks
    allow_fallbacks: true,
    
    // Require all parameters supported
    require_parameters: false,
    
    // Data collection policy
    data_collection: "allow" | "deny",
    
    // Zero Data Retention only
    zdr: false,
    
    // Only allow these providers
    only: ["anthropic"],
    
    // Ignore these providers
    ignore: ["provider-name"],
    
    // Filter by quantization
    quantizations: ["fp16", "int8"],
    
    // Sort by criteria
    sort: "price" | "throughput" | "latency"
  }
})
```

### Default Strategy

**Price-Based Load Balancing** (default):
- Routes to providers with best pricing
- Automatically falls back on failure
- Balances load across top providers

### Provider Preferences Options

| Field | Type | Default | Description |
|-------|-----|---------|-------------|
| `order` | string[] | - | List of provider slugs in preferred order |
| `allow_fallbacks` | boolean | true | Allow backup providers |
| `require_parameters` | boolean | false | Only use providers supporting all parameters |
| `data_collection` | "allow"\|"deny" | "allow" | Control data collection policy |
| `zdr` | boolean | - | Zero Data Retention enforcement |
| `only` | string[] | - | Whitelist of allowed providers |
| `ignore` | string[] | - | Blacklist of providers to skip |
| `quantizations` | string[] | - | Filter by quantization levels |
| `sort` | "price"\|"throughput"\|"latency" | - | Sort criteria for provider selection |

---

## Multimodal Capabilities

### Images

Send images to vision-capable models:

```typescript
mcp_openrouterai_chat_completion({
  model: "google/gemini-2.5-pro",
  messages: [
    {
      role: "user",
      content: [
        { type: "text", text: "What's in this image?" },
        {
          type: "image_url",
          image_url: {
            url: "https://example.com/image.jpg",
            detail: "auto"  // or "low", "high"
          }
        }
      ]
    }
  ]
})
```

**Supported Formats:**
- URLs (recommended for public content)
- Base64-encoded data: `data:image/jpeg;base64,{base64_data}`

**Pricing:** Typically per image or as input tokens

### PDFs

Process PDF documents with any model:

```typescript
mcp_openrouterai_chat_completion({
  model: "anthropic/claude-sonnet-4.5",
  messages: [
    {
      role: "user",
      content: [
        { type: "text", text: "Summarize this PDF" },
        {
          type: "file",
          file: {
            url: "https://example.com/document.pdf"
          }
        }
      ]
    }
  ]
})
```

**Features:**
- Intelligent PDF parsing
- Text extraction (free)
- OCR processing (paid)
- Native model processing

**Pricing:** Free text extraction, paid OCR, or native model pricing

### Audio

Send audio files to speech-capable models:

```typescript
mcp_openrouterai_chat_completion({
  model: "google/gemini-2.5-pro",
  messages: [
    {
      role: "user",
      content: [
        { type: "text", text: "Transcribe this audio" },
        {
          type: "input_audio",
          input_audio: {
            data: base64AudioData,
            format: "wav"  // or "mp3"
          }
        }
      ]
    }
  ]
})
```

**Supported Formats:** `wav`, `mp3`  
**Note:** Audio files must be base64-encoded (URLs not supported)

**Pricing:** Based on audio duration as input tokens

### Image Generation

Generate images from text prompts:

```typescript
mcp_openrouterai_chat_completion({
  model: "google/gemini-2.5-flash-image",
  messages: [
    {
      role: "user",
      content: "Generate an image of a futuristic city at sunset"
    }
  ]
})
```

**Recommended Models:**
1. `google/gemini-2.5-flash-image` - Ultra-cheap, best quality (RECOMMENDED)
2. `openai/gpt-5-image` - Premium quality
3. `openai/gpt-5-image-mini` - Budget-friendly

**Features:**
- Aspect ratio control
- Image editing
- Multi-turn conversations
- Contextual understanding

### Video Support

Video modality support is coming soon (2025).

---

## Tool Calling & Function Calling

OpenRouter standardizes tool calling across all models. Models suggest tools, you execute them, then provide results back.

### Step 1: Request with Tools

```typescript
mcp_openrouterai_chat_completion({
  model: "google/gemini-2.0-flash-001",
  messages: [
    { role: "user", content: "What are some James Joyce books?" }
  ],
  tools: [
    {
      type: "function",
      function: {
        name: "search_gutenberg_books",
        description: "Search for books in Project Gutenberg",
        parameters: {
          type: "object",
          properties: {
            search_terms: {
              type: "array",
              items: { type: "string" },
              description: "List of search terms"
            }
          },
          required: ["search_terms"]
        }
      }
    }
  ]
})
```

### Step 2: Execute Tool Locally

```typescript
// Model responds with tool_calls
const toolCall = response.choices[0].message.tool_calls[0];
const args = JSON.parse(toolCall.function.arguments);
const result = await searchGutenbergBooks(args.search_terms);
```

### Step 3: Provide Tool Results

```typescript
mcp_openrouterai_chat_completion({
  model: "google/gemini-2.0-flash-001",
  messages: [
    { role: "user", content: "What are some James Joyce books?" },
    {
      role: "assistant",
      content: null,
      tool_calls: [
        {
          id: "call_abc123",
          type: "function",
          function: {
            name: "search_gutenberg_books",
            arguments: '{"search_terms": ["James", "Joyce"]}'
          }
        }
      ]
    },
    {
      role: "tool",
      tool_call_id: "call_abc123",
      content: JSON.stringify(result)
    }
  ],
  tools: [...]  // Must include tools in every request
})
```

### Tool Choice Configuration

Control tool usage:

```typescript
// Let model decide (default)
tool_choice: "auto"

// Disable tools
tool_choice: "none"

// Force specific tool
tool_choice: {
  type: "function",
  function: { name: "search_database" }
}
```

### Parallel Tool Calls

Control parallel execution:

```typescript
// Disable parallel - tools called sequentially
parallel_tool_calls: false
```

### Interleaved Thinking

Models can reason between tool calls:

- Enables sophisticated decision-making after receiving results
- Chains multiple tool calls with reasoning steps
- Makes nuanced decisions based on intermediate results
- Increases token usage and latency

**Best Practices:**
- Clear tool descriptions
- Structured parameters
- Context preservation
- Meaningful error messages

---

## Streaming

Enable streaming for all models:

```typescript
mcp_openrouterai_chat_completion({
  model: "anthropic/claude-sonnet-4.5",
  messages: [...],
  stream: true
})
```

**Response Format:**
- Server-Sent Events (SSE)
- Each chunk contains `delta` instead of `message`
- Final chunk contains `usage` object
- May contain "comment" payloads (ignore these)

**Streaming with Tool Calls:**

```typescript
const stream = await mcp_openrouterai_chat_completion({
  model: "anthropic/claude-3.5-sonnet",
  messages: messages,
  tools: tools,
  stream: true
});

// Process stream chunks
// Handle tool_calls in delta
// Execute tools when finish_reason === "tool_calls"
```

---

## Advanced Features

### Assistant Prefill

Guide models to complete partial responses:

```typescript
mcp_openrouterai_chat_completion({
  model: "openai/gpt-5",
  messages: [
    { role: "user", content: "What is the meaning of life?" },
    { role: "assistant", content: "I'm not sure, but my best guess is" }
  ]
})
```

### Prediction

Reduce latency by providing predicted output:

```typescript
mcp_openrouterai_chat_completion({
  model: "openai/gpt-5",
  messages: [...],
  prediction: {
    type: "content",
    content: "Predicted response start..."
  }
})
```

### Model Routing

Specify multiple models to try:

```typescript
mcp_openrouterai_chat_completion({
  models: ["anthropic/claude-sonnet-4.5", "openai/gpt-5"],
  route: "fallback",  // Try first, fallback to second
  messages: [...]
})
```

### Query Generation Stats

Get detailed token counts and costs:

```typescript
// After completion, query by generation ID
const generation = await fetch(
  `https://openrouter.ai/api/v1/generation?id=${generationId}`,
  { headers: { Authorization: `Bearer ${apiKey}` } }
);
```

**Note:** Token counts in API response are normalized (GPT-4o tokenizer). Actual billing uses native tokenizer counts.

---

## Authentication & Security

### API Key Management

**Best Practices:**
- Store API keys in environment variables, never hardcode
- Use secrets management services (AWS Secrets Manager, HashiCorp Vault) for production
- Rotate keys regularly
- Never commit keys to version control

**Access Method:**
```typescript
// Via MCP (recommended - keys managed by Cursor)
mcp_openrouterai_chat_completion({
  model: "...",
  messages: [...]
})

// Direct API (requires OPENROUTER_API_KEY)
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  headers: {
    'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ model, messages })
});
```

### Organizational Security

- Key permissions and usage quotas (if supported)
- Audit logs for team usage
- Per-key rate limits and cost controls

---

## Error Handling & Retry Logic

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request format, parameters |
| 401 | Unauthorized | Verify API key |
| 429 | Rate Limited | Implement exponential backoff |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Retry with backoff |

### Retry Implementation

```typescript
async function chatWithRetry(model: string, messages: any[], maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await mcp_openrouterai_chat_completion({
        model,
        messages
      });
    } catch (error: any) {
      if (error.status === 429 || error.status >= 500) {
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

### Rate Limits

**Types of Rate Limits:**
- **User-level**: Per API key
- **Model-specific**: Varies by model (e.g., GPT-4o vs Llama 3)
- **Provider-level**: Per provider backend

**Rate Limit Headers:**
- Check response headers for rate limit information
- Implement exponential backoff when hitting limits
- Monitor `X-RateLimit-Remaining` if available

### Idempotency

OpenRouter supports idempotency keys to prevent duplicate charges:
```typescript
mcp_openrouterai_chat_completion({
  model: "...",
  messages: [...],
  // Add idempotency key for retries
  // (Check OpenRouter docs for exact parameter name)
});
```

---

## Tokenization & Pricing

### Token Count Differences

Different models tokenize text differently:
- **GPT/Claude/Llama**: Multi-character chunks (common)
- **PaLM**: Character-level tokenization
- **Result**: Same text = different token counts = different costs

**Best Practice**: Use the `usage` field in responses for accurate token counts.

### Cost Calculation

**Pricing Structure:**
- Input tokens: `prompt` price per 1K tokens
- Output tokens: `completion` price per 1K tokens
- Images: Per image or as input tokens
- Audio: Per duration (seconds) or as tokens
- Web search: Per search operation

**Example:**
```typescript
// Model with pricing: $0.000003/1K input, $0.000015/1K output
// Request: 1000 input tokens, 500 output tokens
// Cost = (1000/1000 * 0.000003) + (500/1000 * 0.000015)
// Cost = $0.000003 + $0.0000075 = $0.0000105
```

### Cost Tracking

Query generation stats after completion:
```typescript
// After completion, get detailed stats
const generation = await fetch(
  `https://openrouter.ai/api/v1/generation?id=${generationId}`,
  { headers: { Authorization: `Bearer ${apiKey}` } }
);
// Returns: token counts, costs, provider details
```

---

## Best Practices

### Model Selection

1. **Check Model Availability**: Use `search_models` or `get_model_info` before requesting
2. **Verify Capabilities**: Check `supported_parameters` and `capabilities` flags
3. **Consider Pricing**: Use pricing filters to find cost-effective options
4. **Test Parameters**: Verify model supports required parameters before using
5. **Reference Rankings**: Use `Global-Docs/Universal-Model-Rankings.md` for task-specific selection

### Error Handling

1. **Check Finish Reason**: Handle `length`, `content_filter`, `error` appropriately
2. **Fallback Models**: Use provider routing for automatic fallback
3. **Retry Logic**: Implement exponential backoff for transient failures (see Error Handling section)
4. **Rate Limiting**: Respect rate limits from `per_request_limits`
5. **Idempotency**: Use idempotency keys for retries to prevent duplicate charges

### Performance Optimization

1. **Streaming**: Use streaming for better perceived latency
2. **Caching**: Cache responses when appropriate
3. **Provider Selection**: Use `provider.sort` to optimize for latency/throughput
4. **Context Management**: Use appropriate context lengths (don't oversize)
5. **Token Efficiency**: Monitor token usage and optimize prompts

### Security

1. **Data Policies**: Use `data_collection: "deny"` for sensitive data
2. **ZDR Enforcement**: Use `zdr: true` for Zero Data Retention requirements
3. **User Identification**: Provide `user` parameter for abuse detection
4. **API Key Security**: Never expose API keys in client-side code
5. **Content Moderation**: Understand how content filtering works per provider

### Advanced Features

1. **Seeding**: Use `seed` parameter for reproducible outputs (when supported)
2. **JSON Mode**: Enforce JSON output for structured data (when supported)
3. **Provider-Specific Parameters**: Pass through non-standard parameters when needed
4. **Content Moderation**: Handle moderation responses appropriately

---

## Quick Reference

### Top Models by Use Case

**General Reasoning:**
- `anthropic/claude-sonnet-4.5` - Best overall
- `google/gemini-2.5-pro` - Excellent reasoning
- `openai/gpt-5` - High-stakes accuracy

**Coding:**
- `openai/gpt-5-codex` - Specialized coding
- `anthropic/claude-sonnet-4.5` - Excellent code generation
- `qwen/qwen3-coder-plus` - Open-source coding

**Speed:**
- `x-ai/grok-code-fast-1` - 92 tokens/sec
- `google/gemini-2.5-flash-lite` - Ultra-fast
- `anthropic/claude-haiku-4.5` - Fast with quality

**Cost-Effective:**
- `google/gemini-2.5-flash` - Excellent price/performance
- `deepseek/deepseek-v3.1-terminus` - Open-source, low cost
- `mistralai/mistral-small-3.2-24b-instruct` - Very affordable

**Image Generation:**
- `google/gemini-2.5-flash-image` - RECOMMENDED (ultra-cheap)
- `openai/gpt-5-image` - Premium quality
- `openai/gpt-5-image-mini` - Budget-friendly

**Vision:**
- `google/gemini-2.5-pro` - Native multimodal
- `anthropic/claude-sonnet-4.5` - Excellent vision
- `qwen/qwen3-vl-32b-instruct` - Open-source vision

**Audio:**
- `mistralai/voxtral-small-24b-2507` - Speech transcription
- `google/gemini-2.5-pro` - Native audio support

**Math/Science:**
- `google/gemini-2.5-pro` - Top-tier math
- `openai/o3` - Deep research
- `deepseek/deepseek-r1` - Open-source reasoning

### Common Provider Slugs

- `anthropic` - Anthropic (Claude models)
- `openai` - OpenAI (GPT models)
- `google` - Google (Gemini models)
- `deepseek` - DeepSeek AI
- `x-ai` - xAI (Grok models)
- `mistralai` - Mistral AI
- `qwen` - Alibaba (Qwen models)
- `meta-llama` - Meta (Llama models)
- `z-ai` - Z.AI (GLM models)
- `perplexity` - Perplexity (Sonar models)

### Pricing Structure

Pricing is per token/request/unit:

- **`prompt`**: Cost per input token
- **`completion`**: Cost per output token
- **`request`**: Fixed cost per API request
- **`image`**: Cost per image input
- **`web_search`**: Cost per web search operation
- **`internal_reasoning`**: Cost for reasoning tokens
- **`input_cache_read`**: Cost per cached token read
- **`input_cache_write`**: Cost per cached token write

Value of `"0"` indicates free.

---

## Integration with Startup

This guide is automatically loaded during session startup. Reference it when:

1. Selecting models for tasks
2. Understanding available capabilities
3. Configuring provider routing
4. Using multimodal features
5. Implementing tool calling

**Location**: `Global-Docs/OpenRouter-AI-MCP-Complete-Guide.md`

---

## Related Documentation

- **Universal Model Rankings**: `Global-Docs/Universal-Model-Rankings.md`
- **Minimum Model Levels**: `Global-Workflows/minimum-model-levels.md`
- **OpenRouter API Docs**: https://openrouter.ai/docs
- **OpenRouter Models**: https://openrouter.ai/models

---

**Last Updated**: 2025-11-05  
**Version**: 1.0  
**Status**: Active - Referenced in startup.ps1

