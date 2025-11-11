# Exa MCP Server Setup
**Real-time Web Search and Research Aggregation**

## Overview

Exa is a powerful AI-native search engine designed for developers. The Exa MCP (Model Context Protocol) server provides a standardized interface for integrating Exa's search capabilities into AI applications. This enables real-time web research, content discovery, and knowledge aggregation.

**Created:** October 19, 2025  
**Technology:** Node.js standalone MCP server  
**Purpose:** Deep web research for AI article generation

---

## Prerequisites

- Node.js 18+ installed
- Exa API key from [exa.ai](https://exa.ai)
- Understanding of MCP (Model Context Protocol)
- Cursor AI IDE with MCP support

---

## Installation

### 1. Create Server Directory

```bash
mkdir -p %UserProfile%\.cursor\exa-mcp-server
cd %UserProfile%\.cursor\exa-mcp-server
```

### 2. Initialize Node Project

```bash
npm init -y
```

### 3. Install Dependencies

```bash
npm install exa-js @modelcontextprotocol/sdk
```

### 4. Create Server File

**File:** `index.js`

```javascript
#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const Exa = require('exa-js').default;

// Initialize Exa client
const exa = new Exa(process.env.EXA_API_KEY);

// Create MCP server
const server = new Server(
  {
    name: 'exa-mcp-server',
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
        name: 'search',
        description: 'Search the web using Exa AI. Returns high-quality, AI-native search results with content.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'The search query',
            },
            numResults: {
              type: 'number',
              description: 'Number of results to return (default: 10, max: 100)',
              default: 10,
            },
            includeDomains: {
              type: 'array',
              items: { type: 'string' },
              description: 'Optional list of domains to include in search',
            },
            excludeDomains: {
              type: 'array',
              items: { type: 'string' },
              description: 'Optional list of domains to exclude from search',
            },
            startPublishedDate: {
              type: 'string',
              description: 'Start date for published content (ISO 8601 format)',
            },
            endPublishedDate: {
              type: 'string',
              description: 'End date for published content (ISO 8601 format)',
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'search_similar',
        description: 'Find content similar to a given URL using Exa AI',
        inputSchema: {
          type: 'object',
          properties: {
            url: {
              type: 'string',
              description: 'The URL to find similar content for',
            },
            numResults: {
              type: 'number',
              description: 'Number of results to return (default: 10)',
              default: 10,
            },
          },
          required: ['url'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === 'search') {
      const options = {
        numResults: args.numResults || 10,
        type: 'auto',
        text: true,
        highlights: true,
      };

      if (args.includeDomains) options.includeDomains = args.includeDomains;
      if (args.excludeDomains) options.excludeDomains = args.excludeDomains;
      if (args.startPublishedDate) options.startPublishedDate = args.startPublishedDate;
      if (args.endPublishedDate) options.endPublishedDate = args.endPublishedDate;

      const results = await exa.searchAndContents(args.query, options);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } else if (name === 'search_similar') {
      const results = await exa.findSimilarAndContents(args.url, {
        numResults: args.numResults || 10,
        text: true,
        highlights: true,
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
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
  console.error('Exa MCP server running on stdio');
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
    "exa": {
      "command": "node",
      "args": [
        "%UserProfile%\\.cursor\\exa-mcp-server\\index.js"
      ],
      "env": {
        "EXA_API_KEY": "your-exa-api-key-here"
      }
    }
  }
}
```

**For Linux/Mac:**
```json
{
  "mcpServers": {
    "exa": {
      "command": "node",
      "args": [
        "$HOME/.cursor/exa-mcp-server/index.js"
      ],
      "env": {
        "EXA_API_KEY": "your-exa-api-key-here"
      }
    }
  }
}
```

---

## Usage

### In TypeScript/JavaScript

**File:** `lib/ai/exa-client.ts`

```typescript
export interface ExaSearchOptions {
  query: string;
  numResults?: number;
  includeDomains?: string[];
  excludeDomains?: string[];
  startPublishedDate?: string;
  endPublishedDate?: string;
}

export interface ExaSearchResult {
  title: string;
  url: string;
  publishedDate: string;
  author?: string;
  text: string;
  highlights: string[];
  score: number;
}

/**
 * Search the web using Exa AI via MCP
 */
export async function searchExa(
  options: ExaSearchOptions
): Promise<ExaSearchResult[]> {
  try {
    // Call MCP tool (implementation depends on your MCP client)
    const response = await callMCPTool('exa', 'search', {
      query: options.query,
      numResults: options.numResults || 10,
      includeDomains: options.includeDomains,
      excludeDomains: options.excludeDomains,
      startPublishedDate: options.startPublishedDate,
      endPublishedDate: options.endPublishedDate,
    });

    const data = JSON.parse(response.content[0].text);
    return data.results;
  } catch (error) {
    console.error('Exa search error:', error);
    throw error;
  }
}

/**
 * Find similar content to a URL
 */
export async function searchSimilar(
  url: string,
  numResults: number = 10
): Promise<ExaSearchResult[]> {
  try {
    const response = await callMCPTool('exa', 'search_similar', {
      url,
      numResults,
    });

    const data = JSON.parse(response.content[0].text);
    return data.results;
  } catch (error) {
    console.error('Exa similar search error:', error);
    throw error;
  }
}
```

### Example: Research AI Topics

```typescript
import { searchExa } from './lib/ai/exa-client';

// Search for recent AI research
const results = await searchExa({
  query: 'artificial intelligence medical diagnostics',
  numResults: 20,
  includeDomains: ['arxiv.org', 'nature.com', 'sciencedirect.com'],
  startPublishedDate: '2024-01-01',
});

console.log(`Found ${results.length} research papers`);

for (const result of results) {
  console.log(`\nTitle: ${result.title}`);
  console.log(`URL: ${result.url}`);
  console.log(`Published: ${result.publishedDate}`);
  console.log(`Highlights: ${result.highlights.join(' ... ')}`);
}
```

---

## API Reference

### search

Search the web using Exa AI with advanced filtering.

**Parameters:**
- `query` (string, required): The search query
- `numResults` (number, optional): Number of results (default: 10, max: 100)
- `includeDomains` (string[], optional): Whitelist domains
- `excludeDomains` (string[], optional): Blacklist domains
- `startPublishedDate` (string, optional): ISO 8601 date (e.g., "2024-01-01")
- `endPublishedDate` (string, optional): ISO 8601 date

**Returns:**
```typescript
{
  results: [
    {
      title: string;
      url: string;
      publishedDate: string;
      author?: string;
      text: string;           // Full content
      highlights: string[];   // Relevant excerpts
      score: number;          // Relevance score
    }
  ]
}
```

### search_similar

Find content similar to a given URL.

**Parameters:**
- `url` (string, required): The reference URL
- `numResults` (number, optional): Number of results (default: 10)

**Returns:** Same format as `search`

---

## Best Practices

### 1. Query Optimization

```typescript
// ✅ Good: Specific, focused query
await searchExa({
  query: 'transformer architecture attention mechanism',
  numResults: 10,
});

// ❌ Bad: Too broad, vague
await searchExa({
  query: 'AI',
  numResults: 100,
});
```

### 2. Domain Filtering

```typescript
// Research papers only
await searchExa({
  query: 'quantum machine learning',
  includeDomains: [
    'arxiv.org',
    'nature.com',
    'science.org',
    'ieee.org',
  ],
});

// Exclude social media
await searchExa({
  query: 'AI news',
  excludeDomains: [
    'twitter.com',
    'reddit.com',
    'facebook.com',
  ],
});
```

### 3. Date Filtering

```typescript
// Last 6 months only
const sixMonthsAgo = new Date();
sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

await searchExa({
  query: 'GPT-4 benchmarks',
  startPublishedDate: sixMonthsAgo.toISOString().split('T')[0],
  numResults: 20,
});
```

### 4. Error Handling

```typescript
async function robustSearch(query: string) {
  const maxRetries = 3;
  let lastError;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await searchExa({ query, numResults: 10 });
    } catch (error) {
      lastError = error;
      console.log(`Retry ${i + 1}/${maxRetries} for query: ${query}`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }

  throw new Error(`Failed after ${maxRetries} retries: ${lastError.message}`);
}
```

---

## Troubleshooting

### Server Won't Start

**Error:** `Cannot find module 'exa-js'`

**Solution:**
```bash
cd %UserProfile%\.cursor\exa-mcp-server
npm install exa-js @modelcontextprotocol/sdk
```

### API Key Invalid

**Error:** `401 Unauthorized`

**Solution:**
1. Verify API key at [exa.ai dashboard](https://dashboard.exa.ai)
2. Check mcp.json has correct key
3. Restart Cursor IDE

### No Results Returned

**Possible Causes:**
- Query too specific/narrow
- Domain filters too restrictive
- Date range excludes all content

**Solutions:**
- Broaden query terms
- Remove or adjust domain filters
- Expand date range

### Connection Timeout

**Error:** `ETIMEDOUT` or `ECONNREFUSED`

**Solutions:**
- Check internet connection
- Verify firewall settings
- Test with curl:
```bash
curl -X POST https://api.exa.ai/search \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "numResults": 1}'
```

---

## Performance Optimization

### Caching Results

```typescript
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 3600000; // 1 hour

async function cachedSearch(query: string) {
  const cacheKey = JSON.stringify({ query });
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    console.log('Cache hit:', query);
    return cached.data;
  }

  const results = await searchExa({ query, numResults: 10 });
  cache.set(cacheKey, { data: results, timestamp: Date.now() });
  return results;
}
```

### Rate Limiting

```typescript
import pLimit from 'p-limit';

// Limit to 5 concurrent searches
const limit = pLimit(5);

const queries = ['AI research', 'ML algorithms', 'deep learning'];
const results = await Promise.all(
  queries.map(query => 
    limit(() => searchExa({ query, numResults: 5 }))
  )
);
```

---

## Advanced Features

### Highlighting Important Content

```typescript
function extractKeyInsights(results: ExaSearchResult[]): string[] {
  const insights: string[] = [];

  for (const result of results) {
    // Highlights are the most relevant excerpts
    insights.push(...result.highlights);
  }

  // Remove duplicates and sort by relevance
  return [...new Set(insights)]
    .sort((a, b) => b.length - a.length)
    .slice(0, 10);
}
```

### Domain-Specific Research

```typescript
const academicDomains = [
  'arxiv.org',
  'nature.com',
  'sciencedirect.com',
  'ieee.org',
  'acm.org',
  'springer.com',
];

async function academicResearch(topic: string) {
  return searchExa({
    query: topic,
    includeDomains: academicDomains,
    startPublishedDate: '2023-01-01',
    numResults: 30,
  });
}
```

---

## Security Considerations

1. **Never commit API keys** - Use environment variables
2. **Validate search queries** - Sanitize user input
3. **Rate limit requests** - Prevent API abuse
4. **Cache results** - Reduce API calls and costs
5. **Monitor usage** - Track API consumption

---

## Related Documentation

- [AI-COLLABORATIVE-AUTHORING-SYSTEM.md](./AI-COLLABORATIVE-AUTHORING-SYSTEM.md) - Main system overview
- [PERPLEXITY-ASK-MCP-SERVER-SETUP.md](./PERPLEXITY-ASK-MCP-SERVER-SETUP.md) - Companion research tool
- Official Exa Documentation: https://docs.exa.ai

---

**Last Updated:** October 19, 2025  
**Maintained By:** AI Development Team

