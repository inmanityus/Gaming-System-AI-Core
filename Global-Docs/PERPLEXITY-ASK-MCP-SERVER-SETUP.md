# Perplexity Ask MCP Server Setup
**AI-Powered Research Synthesis with Citations**

## Overview

Perplexity AI is an advanced AI-powered answer engine that synthesizes information from multiple sources and provides citations. The Perplexity Ask MCP server provides a standardized interface for integrating Perplexity's research capabilities, enabling AI systems to get authoritative answers with source attribution.

**Created:** October 19, 2025  
**Technology:** Node.js standalone MCP server  
**Purpose:** Research synthesis and fact verification for AI article generation

---

## Prerequisites

- Node.js 18+ installed
- Perplexity API key from [perplexity.ai](https://www.perplexity.ai)
- Understanding of MCP (Model Context Protocol)
- Cursor AI IDE with MCP support

---

## Installation

### 1. Create Server Directory

```bash
mkdir -p %UserProfile%\.cursor\perplexity-ask-mcp
cd %UserProfile%\.cursor\perplexity-ask-mcp
```

### 2. Initialize Node Project

```bash
npm init -y
```

### 3. Install Dependencies

```bash
npm install axios @modelcontextprotocol/sdk
```

### 4. Create Server File

**File:** `index.js`

```javascript
#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const axios = require('axios');

// Perplexity API configuration
const PERPLEXITY_API_URL = 'https://api.perplexity.ai/chat/completions';
const API_KEY = process.env.PERPLEXITY_API_KEY;

// Create MCP server
const server = new Server(
  {
    name: 'perplexity-ask-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'ask',
        description: 'Ask Perplexity AI a question and get a researched answer with citations. Perfect for factual research and technical questions.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'The question to ask Perplexity AI',
            },
            model: {
              type: 'string',
              description: 'Model to use (default: llama-3.1-sonar-large-128k-online)',
              enum: [
                'llama-3.1-sonar-small-128k-online',
                'llama-3.1-sonar-large-128k-online',
                'llama-3.1-sonar-huge-128k-online',
              ],
              default: 'llama-3.1-sonar-large-128k-online',
            },
            searchDomainFilter: {
              type: 'array',
              items: { type: 'string' },
              description: 'Optional domains to search within',
            },
            returnCitations: {
              type: 'boolean',
              description: 'Whether to return source citations (default: true)',
              default: true,
            },
          },
          required: ['query'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === 'ask') {
      const model = args.model || 'llama-3.1-sonar-large-128k-online';
      
      const payload = {
        model: model,
        messages: [
          {
            role: 'system',
            content: 'You are a helpful research assistant. Provide detailed, well-researched answers with citations.',
          },
          {
            role: 'user',
            content: args.query,
          },
        ],
        temperature: 0.2,
        top_p: 0.9,
        return_citations: args.returnCitations !== false,
        search_domain_filter: args.searchDomainFilter || [],
      };

      const response = await axios.post(PERPLEXITY_API_URL, payload, {
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 second timeout
      });

      const result = {
        answer: response.data.choices[0].message.content,
        citations: response.data.citations || [],
        model: model,
        usage: response.data.usage,
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    const errorMessage = error.response?.data?.error?.message || error.message;
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Perplexity Ask MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
```

### 5. Make Executable (Unix/Mac)

```bash
chmod +x index.js
```

---

## Configuration

### MCP Configuration File

**Location:** `%UserProfile%\.cursor\mcp.json`

```json
{
  "mcpServers": {
    "perplexity-ask": {
      "command": "node",
      "args": [
        "%UserProfile%\\.cursor\\perplexity-ask-mcp\\index.js"
      ],
      "env": {
        "PERPLEXITY_API_KEY": "your-perplexity-api-key-here"
      }
    }
  }
}
```

**For Linux/Mac:**
```json
{
  "mcpServers": {
    "perplexity-ask": {
      "command": "node",
      "args": [
        "$HOME/.cursor/perplexity-ask-mcp/index.js"
      ],
      "env": {
        "PERPLEXITY_API_KEY": "your-perplexity-api-key-here"
      }
    }
  }
}
```

---

## Usage

### In TypeScript/JavaScript

**File:** `lib/ai/perplexity-client.ts`

```typescript
export interface PerplexityAskOptions {
  query: string;
  model?: 'llama-3.1-sonar-small-128k-online' | 'llama-3.1-sonar-large-128k-online' | 'llama-3.1-sonar-huge-128k-online';
  searchDomainFilter?: string[];
  returnCitations?: boolean;
}

export interface PerplexityResponse {
  answer: string;
  citations: string[];
  model: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/**
 * Ask Perplexity AI a question via MCP
 */
export async function askPerplexity(
  options: PerplexityAskOptions
): Promise<PerplexityResponse> {
  try {
    // Call MCP tool (implementation depends on your MCP client)
    const response = await callMCPTool('perplexity-ask', 'ask', {
      query: options.query,
      model: options.model || 'llama-3.1-sonar-large-128k-online',
      searchDomainFilter: options.searchDomainFilter,
      returnCitations: options.returnCitations !== false,
    });

    return JSON.parse(response.content[0].text);
  } catch (error) {
    console.error('Perplexity ask error:', error);
    throw error;
  }
}
```

### Example: Technical Research

```typescript
import { askPerplexity } from './lib/ai/perplexity-client';

// Ask about AI medical diagnostics
const response = await askPerplexity({
  query: 'What are the latest breakthroughs in AI-powered medical diagnostics?',
  model: 'llama-3.1-sonar-large-128k-online',
  searchDomainFilter: ['nature.com', 'sciencedirect.com', 'ieee.org'],
  returnCitations: true,
});

console.log('Answer:', response.answer);
console.log('\nCitations:');
response.citations.forEach((citation, i) => {
  console.log(`${i + 1}. ${citation}`);
});
```

---

## API Reference

### ask

Ask Perplexity AI a question and receive a synthesized answer with citations.

**Parameters:**
- `query` (string, required): The question to ask
- `model` (string, optional): Model to use (default: llama-3.1-sonar-large-128k-online)
  - `llama-3.1-sonar-small-128k-online`: Fastest, good for simple queries
  - `llama-3.1-sonar-large-128k-online`: Balanced performance and quality
  - `llama-3.1-sonar-huge-128k-online`: Highest quality, slowest
- `searchDomainFilter` (string[], optional): Limit search to specific domains
- `returnCitations` (boolean, optional): Include source citations (default: true)

**Returns:**
```typescript
{
  answer: string;           // Synthesized answer
  citations: string[];      // Source URLs
  model: string;           // Model used
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}
```

---

## Model Selection Guide

### llama-3.1-sonar-small-128k-online
- **Speed:** Fast (~2-5 seconds)
- **Quality:** Good for straightforward questions
- **Cost:** Lowest
- **Best For:** Simple factual queries, quick lookups

### llama-3.1-sonar-large-128k-online (Recommended)
- **Speed:** Moderate (~5-10 seconds)
- **Quality:** Excellent balance
- **Cost:** Medium
- **Best For:** Technical research, detailed explanations

### llama-3.1-sonar-huge-128k-online
- **Speed:** Slower (~10-20 seconds)
- **Quality:** Highest quality, most comprehensive
- **Cost:** Highest
- **Best For:** Complex research, academic papers, critical decisions

---

## Best Practices

### 1. Query Formulation

```typescript
// ✅ Good: Specific, well-formed question
await askPerplexity({
  query: 'What are the key architectural differences between GPT-4 and Claude 3, and how do they impact performance?',
});

// ❌ Bad: Too vague
await askPerplexity({
  query: 'AI models',
});
```

### 2. Domain Filtering for Authority

```typescript
// Academic research only
await askPerplexity({
  query: 'quantum machine learning applications',
  searchDomainFilter: [
    'arxiv.org',
    'nature.com',
    'sciencedirect.com',
    'ieee.org',
  ],
});

// News and media
await askPerplexity({
  query: 'latest AI regulations',
  searchDomainFilter: [
    'reuters.com',
    'bloomberg.com',
    'techcrunch.com',
  ],
});
```

### 3. Citation Handling

```typescript
async function askWithCitations(question: string) {
  const response = await askPerplexity({
    query: question,
    returnCitations: true,
  });

  // Format answer with inline citations
  let formatted = response.answer;
  response.citations.forEach((citation, i) => {
    formatted += `\n[${i + 1}] ${citation}`;
  });

  return formatted;
}
```

### 4. Error Handling with Retry

```typescript
async function robustAsk(query: string, maxRetries: number = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await askPerplexity({ query });
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      console.log(`Retry ${i + 1}/${maxRetries}`);
      await new Promise(resolve => 
        setTimeout(resolve, Math.pow(2, i) * 1000)
      );
    }
  }
}
```

---

## Advanced Usage

### Multi-Question Research

```typescript
async function comprehensiveResearch(topic: string) {
  const questions = [
    `What is ${topic}?`,
    `What are the latest developments in ${topic}?`,
    `What are the main challenges in ${topic}?`,
    `What are the future trends for ${topic}?`,
  ];

  const responses = await Promise.all(
    questions.map(q => askPerplexity({ query: q }))
  );

  return {
    overview: responses[0].answer,
    developments: responses[1].answer,
    challenges: responses[2].answer,
    trends: responses[3].answer,
    citations: [...new Set(responses.flatMap(r => r.citations))],
  };
}
```

### Fact Verification

```typescript
async function verifyFact(claim: string) {
  const response = await askPerplexity({
    query: `Is this claim accurate: "${claim}"? Provide evidence.`,
    returnCitations: true,
  });

  return {
    claim,
    verification: response.answer,
    sources: response.citations,
  };
}
```

### Domain-Specific Expert

```typescript
async function askMedicalExpert(question: string) {
  return askPerplexity({
    query: `From a medical research perspective: ${question}`,
    searchDomainFilter: [
      'pubmed.ncbi.nlm.nih.gov',
      'nejm.org',
      'thelancet.com',
      'nature.com',
    ],
    model: 'llama-3.1-sonar-huge-128k-online', // Highest quality for medical
  });
}
```

---

## Integration with Article Generation

### Research Phase Integration

```typescript
import { askPerplexity } from './lib/ai/perplexity-client';
import { searchExa } from './lib/ai/exa-client';

async function comprehensiveResearch(keywords: string[]) {
  const keywordString = keywords.join(', ');

  // Parallel research
  const [perplexityData, exaData] = await Promise.all([
    // Get synthesized overview
    askPerplexity({
      query: `Provide a comprehensive overview of ${keywordString}, including recent developments, key applications, and technical challenges.`,
      model: 'llama-3.1-sonar-large-128k-online',
    }),
    
    // Get specific sources
    searchExa({
      query: keywordString,
      numResults: 20,
      startPublishedDate: '2024-01-01',
    }),
  ]);

  return {
    overview: perplexityData.answer,
    citations: perplexityData.citations,
    sources: exaData,
  };
}
```

---

## Troubleshooting

### API Key Issues

**Error:** `401 Unauthorized`

**Solutions:**
1. Verify API key at [Perplexity Console](https://www.perplexity.ai/settings/api)
2. Check mcp.json configuration
3. Ensure no extra spaces/characters in key
4. Restart Cursor IDE

### Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:**
```typescript
import pLimit from 'p-limit';

// Limit concurrent requests
const limit = pLimit(3); // Max 3 concurrent

const questions = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'];
const results = await Promise.all(
  questions.map(q => 
    limit(() => askPerplexity({ query: q }))
  )
);
```

### Timeout Errors

**Error:** `ETIMEDOUT`

**Solutions:**
1. Increase timeout in server code (default: 30s)
2. Use smaller model for faster responses
3. Simplify query
4. Check internet connection

### Poor Quality Answers

**Solutions:**
1. Use larger model (huge instead of small)
2. Add domain filters for authority sources
3. Rephrase question more specifically
4. Break complex questions into parts

---

## Performance Optimization

### Caching

```typescript
const answerCache = new Map<string, { data: any; expires: number }>();

async function cachedAsk(query: string, ttl: number = 86400000) {
  const cached = answerCache.get(query);
  
  if (cached && Date.now() < cached.expires) {
    return cached.data;
  }

  const response = await askPerplexity({ query });
  answerCache.set(query, {
    data: response,
    expires: Date.now() + ttl,
  });

  return response;
}
```

### Batch Processing

```typescript
async function batchResearch(topics: string[]) {
  const batchSize = 5;
  const results = [];

  for (let i = 0; i < topics.length; i += batchSize) {
    const batch = topics.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(topic => askPerplexity({ query: topic }))
    );
    results.push(...batchResults);
    
    // Small delay between batches
    if (i + batchSize < topics.length) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  return results;
}
```

---

## Comparison: Perplexity vs Exa

| Feature | Perplexity Ask | Exa Search |
|---------|---------------|------------|
| **Purpose** | Synthesized answers | Raw sources |
| **Citations** | Automatic | Manual extraction |
| **Speed** | Moderate (5-10s) | Fast (1-3s) |
| **Output** | Prose answer | Structured data |
| **Best For** | Questions | Discovery |
| **Cost** | Higher | Lower |

**When to Use Each:**
- **Perplexity:** Need authoritative answer with synthesis
- **Exa:** Need multiple sources for manual analysis
- **Both:** Comprehensive research (Exa for sources, Perplexity for synthesis)

---

## Security Considerations

1. **API Key Protection**
   - Never commit to version control
   - Use environment variables
   - Rotate keys regularly

2. **Query Validation**
   - Sanitize user input
   - Limit query length
   - Filter sensitive information

3. **Rate Limiting**
   - Implement request throttling
   - Monitor API usage
   - Set spending limits

4. **Citation Verification**
   - Always verify critical facts
   - Check citation accessibility
   - Cross-reference multiple sources

---

## Cost Management

### Pricing Tiers (Approximate)

- **Small Model:** ~$0.20 per 1M tokens
- **Large Model:** ~$1.00 per 1M tokens
- **Huge Model:** ~$5.00 per 1M tokens

### Cost Optimization Strategies

1. **Use appropriate model size**
2. **Cache frequent queries**
3. **Batch similar questions**
4. **Limit citation returns when not needed**
5. **Monitor usage with logging**

```typescript
let totalCost = 0;

async function trackedAsk(query: string) {
  const response = await askPerplexity({ query });
  
  const cost = (response.usage.total_tokens / 1000000) * 1.00; // $1/M tokens
  totalCost += cost;
  
  console.log(`Query cost: $${cost.toFixed(4)}, Total: $${totalCost.toFixed(2)}`);
  return response;
}
```

---

## Related Documentation

- [AI-COLLABORATIVE-AUTHORING-SYSTEM.md](./AI-COLLABORATIVE-AUTHORING-SYSTEM.md) - Main system overview
- [EXA-MCP-SERVER-SETUP.md](./EXA-MCP-SERVER-SETUP.md) - Companion research tool
- Official Perplexity Documentation: https://docs.perplexity.ai

---

**Last Updated:** October 19, 2025  
**Maintained By:** AI Development Team

