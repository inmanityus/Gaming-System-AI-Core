# Token Window Management System

A production-ready system for preventing AI model crashes due to token limit exhaustion. This service proactively manages conversation context, implements intelligent compression strategies, and handles streaming responses to ensure continuous AI operation.

## Features

- **Proactive Token Management**: Monitors token usage and compresses context before hitting limits
- **Multiple Compression Strategies**: Summarization, sliding window, and hybrid approaches
- **Multi-Model Support**: Works with OpenAI, Anthropic, Google, and custom models
- **Streaming Support**: Efficient streaming for real-time responses
- **Session Management**: Tracks conversation state across multiple sessions
- **Automatic Failsafe**: Emergency compression to prevent crashes
- **Model-Agnostic**: Easy to add new models and providers

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Client    │────▶│   API Gateway   │────▶│   Session    │
│             │     │ (FastAPI)       │     │   Manager    │
└─────────────┘     └─────────────────┘     └──────────────┘
                            │                       │
                            ▼                       ▼
                    ┌──────────────┐        ┌──────────────┐
                    │   Context    │◀───────│    State     │
                    │   Engine     │        │    Store     │
                    └──────────────┘        └──────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │  Tokenizer   │        │   Context    │
        │  Service     │        │  Strategy    │
        └──────────────┘        └──────────────┘
                                        │
                                        ▼
                                ┌──────────────┐
                                │     LLM      │
                                │   Gateway    │
                                └──────────────┘
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd services/token_management

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key
export GOOGLE_API_KEY=your_google_key
```

### Running the Service

```bash
# Development
uvicorn api:app --reload --port 8080

# Production
uvicorn api:app --host 0.0.0.0 --port 8080 --workers 4
```

### Using the Client

```python
from token_management.client import TokenManagementClient

async with TokenManagementClient() as client:
    # Start a conversation
    session_id = "user_123_session_456"
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a long story."}
    ]
    
    # Stream response with automatic token management
    async for chunk in await client.create_completion(
        session_id=session_id,
        messages=messages,
        model="gpt-4o",
        stream=True
    ):
        print(chunk, end="")
```

## API Endpoints

### Chat Completion
```http
POST /chat/completions
Content-Type: application/json

{
    "session_id": "user_123",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "model": "gpt-4o",
    "temperature": 0.7,
    "stream": true
}
```

### Token Counting
```http
POST /tokens/count
Content-Type: application/json

{
    "text": "Count tokens in this text",
    "model": "gpt-4"
}
```

### Session Management
```http
GET /sessions/{session_id}  # Get session info
GET /sessions               # List all sessions
DELETE /sessions/{session_id} # Delete session
```

### System Information
```http
GET /metrics  # Get system metrics
GET /models   # List available models
```

## Configuration

### Model Token Windows

| Model | Input Window | Max Output | Total Window |
|-------|-------------|------------|--------------|
| GPT-4o | 128,000 | 4,096 | 128,000 |
| Claude 3.5 Sonnet | 200,000 | 8,192 | 200,000 |
| Gemini 1.5 Pro | 1,000,000 | 8,192 | 1,000,000 |

### Compression Strategies

1. **Summarization**: Creates AI-generated summaries of older messages
2. **Sliding Window**: Keeps only the most recent messages
3. **Hybrid**: Combines summarization for old messages with sliding window for recent ones

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GOOGLE_API_KEY`: Google API key
- `DEFAULT_STRATEGY`: Default compression strategy (hybrid, summarization, sliding_window)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

## Deployment

### Docker

```bash
# Build image
docker build -t token-management .

# Run container
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  token-management
```

### AWS ECS

```bash
# Deploy to ECS
./deploy.sh
```

## Monitoring

The system provides comprehensive metrics:

- Active sessions count
- Compressions performed
- Tokens saved through compression
- Potential crashes prevented
- API call statistics
- Error rates

Access metrics at: `GET /metrics`

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=token_management

# Run specific test
pytest tests/test_token_management.py::TestContextEngine
```

## Best Practices

1. **Session Management**: Use consistent session IDs for conversations
2. **Model Selection**: Choose models based on context window needs
3. **Monitoring**: Track token usage and compression metrics
4. **Cleanup**: Periodically clean up old sessions
5. **Error Handling**: Implement retry logic for API failures

## Troubleshooting

### Common Issues

1. **Token Limit Errors**
   - Check if compression is triggered (view metrics)
   - Verify model configuration is correct
   - Ensure session state is properly maintained

2. **Slow Response Times**
   - Enable streaming for better perceived performance
   - Check if summarization is taking too long
   - Consider using sliding window strategy

3. **Memory Issues**
   - Enable automatic session cleanup
   - Reduce session retention period
   - Monitor active session count

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Your License Here]
