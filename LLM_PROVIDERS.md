# LLM Provider Configuration Guide

The agentic system supports multiple LLM providers, allowing you to choose the best model for your use case based on cost, performance, and availability.

## Supported Providers

### 1. OpenAI
- **Models**: GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo
- **Best for**: High-quality responses, reliable JSON output
- **Cost**: $$$ (most expensive)
- **Get API key**: https://platform.openai.com/api-keys

### 2. OpenRouter
- **Models**: Claude 3.5 Sonnet, Gemini Pro, Llama 3.1, and 200+ others
- **Best for**: Access to multiple providers through one API, competitive pricing
- **Cost**: $ to $$ (varies by model)
- **Get API key**: https://openrouter.ai/keys

### 3. DeepSeek
- **Models**: DeepSeek Chat, DeepSeek Coder
- **Best for**: Cost-effective alternative, good for coding tasks
- **Cost**: $ (very affordable)
- **Get API key**: https://platform.deepseek.com/

### 4. Google Gemini
- **Models**: Gemini Pro, Gemini 1.5 Pro, Gemini 1.5 Flash
- **Best for**: Fast responses, multimodal capabilities
- **Cost**: $ to $$ (competitive pricing)
- **Get API key**: https://makersuite.google.com/app/apikey

## Configuration

### Quick Setup

1. **Choose your provider** by setting `LLM_PROVIDER` in `backend/.env`:
   ```bash
   LLM_PROVIDER=openai  # or: openrouter, deepseek, gemini
   ```

2. **Set the API key** for your chosen provider:
   ```bash
   # For OpenAI
   OPENAI_API_KEY=sk-your-key-here
   
   # For OpenRouter
   OPENROUTER_API_KEY=sk-or-your-key
   
   # For DeepSeek
   DEEPSEEK_API_KEY=sk-your-key
   
   # For Gemini
   GEMINI_API_KEY=your-key
   ```

3. **Configure the model**:
   ```bash
   LLM_MODEL=gpt-4o  # or your preferred model
   LLM_TEMPERATURE=0.2
   ```

### Provider-Specific Examples

#### OpenAI

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.2
OPENAI_API_KEY=sk-proj-xxxxx
```

**Recommended models:**
- `gpt-4o` - Best balance of quality and speed
- `gpt-4-turbo` - High quality, slower
- `gpt-3.5-turbo` - Fast and cheap

#### OpenRouter

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.2
OPENROUTER_API_KEY=sk-or-xxxxx
```

**Recommended models:**
- `anthropic/claude-3.5-sonnet` - Excellent reasoning
- `google/gemini-pro-1.5` - Good quality, fast
- `meta-llama/llama-3.1-70b-instruct` - Open source, cost-effective
- `openai/gpt-4o` - Access OpenAI through OpenRouter

See full model list: https://openrouter.ai/models

#### DeepSeek

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2
DEEPSEEK_API_KEY=sk-xxxxx
```

**Available models:**
- `deepseek-chat` - General purpose chat model
- `deepseek-coder` - Optimized for code generation

#### Google Gemini

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-pro
LLM_TEMPERATURE=0.2
GEMINI_API_KEY=AIzaSyXXXXX
```

**Recommended models:**
- `gemini-1.5-pro` - Best quality
- `gemini-1.5-flash` - Fastest, cheapest
- `gemini-pro` - Previous generation, still good

### Advanced Configuration

#### Custom OpenAI-Compatible Endpoints

If you're using a self-hosted or custom OpenAI-compatible API:

```bash
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://your-custom-endpoint.com/v1
OPENAI_API_KEY=your-key
```

#### Custom OpenRouter Endpoint

```bash
LLM_PROVIDER=openrouter
OPENROUTER_BASE_URL=https://your-custom-proxy.com/api/v1
OPENROUTER_API_KEY=your-key
```

#### Multiple Providers (for fallback)

You can configure multiple providers simultaneously. The system uses `LLM_PROVIDER` to select the active one, but you can switch by changing the environment variable:

```bash
# Configure all providers
OPENAI_API_KEY=sk-proj-xxxxx
OPENROUTER_API_KEY=sk-or-xxxxx
DEEPSEEK_API_KEY=sk-xxxxx
GEMINI_API_KEY=AIzaSyXXXXX

# Select active provider
LLM_PROVIDER=openai  # Change this to switch providers
```

## API Endpoints

### Check Provider Status

```bash
GET /api/agentic/status
```

Returns current provider configuration and status of all configured providers:

```json
{
  "enabled": true,
  "current_provider": "openai",
  "current_model": "gpt-4o",
  "temperature": 0.2,
  "provider_configured": true,
  "mongo_configured": true,
  "providers": {
    "openai": {
      "configured": true,
      "endpoint": "https://api.openai.com/v1",
      "example_models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    "openrouter": {
      "configured": false,
      "endpoint": "https://openrouter.ai/api/v1",
      "example_models": [...]
    },
    ...
  }
}
```

### Get Detailed Provider Info

```bash
GET /api/agentic/providers
```

Returns comprehensive information about all providers and their configuration.

## Cost Comparison

Approximate costs per 1M tokens (as of Nov 2024):

| Provider | Model | Input | Output | Total (avg) |
|----------|-------|-------|--------|-------------|
| OpenAI | GPT-4o | $2.50 | $10.00 | $6.25 |
| OpenAI | GPT-4 Turbo | $10.00 | $30.00 | $20.00 |
| OpenAI | GPT-3.5 Turbo | $0.50 | $1.50 | $1.00 |
| OpenRouter | Claude 3.5 Sonnet | $3.00 | $15.00 | $9.00 |
| OpenRouter | Gemini Pro 1.5 | $1.25 | $5.00 | $3.13 |
| OpenRouter | Llama 3.1 70B | $0.35 | $0.40 | $0.38 |
| DeepSeek | DeepSeek Chat | $0.14 | $0.28 | $0.21 |
| Gemini | Gemini 1.5 Pro | $1.25 | $5.00 | $3.13 |
| Gemini | Gemini 1.5 Flash | $0.075 | $0.30 | $0.19 |

**Note**: Prices vary and may change. Check provider websites for current pricing.

### Estimated Cost per Analysis

Each agentic analysis makes approximately **5-6 LLM calls** (orchestrator + 4 sub-agents). Average tokens per analysis: ~15,000 (input + output).

| Provider | Cost per Analysis |
|----------|-------------------|
| OpenAI GPT-4o | $0.09 - $0.12 |
| OpenAI GPT-3.5 Turbo | $0.015 - $0.02 |
| OpenRouter Claude 3.5 | $0.13 - $0.17 |
| OpenRouter Llama 3.1 | $0.006 - $0.008 |
| DeepSeek Chat | $0.003 - $0.004 |
| Gemini 1.5 Flash | $0.003 - $0.004 |

## Performance Comparison

Based on typical disruption analysis workload:

| Provider | Model | Latency | Quality | JSON Reliability |
|----------|-------|---------|---------|------------------|
| OpenAI | GPT-4o | ⚡⚡⚡ Fast | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent |
| OpenAI | GPT-3.5 Turbo | ⚡⚡⚡⚡ Very Fast | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Very Good |
| OpenRouter | Claude 3.5 | ⚡⚡ Moderate | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Very Good |
| OpenRouter | Llama 3.1 70B | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐ Good |
| DeepSeek | Chat | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐ Good |
| Gemini | 1.5 Pro | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐⭐ Very Good |
| Gemini | 1.5 Flash | ⚡⚡⚡⚡⚡ Blazing | ⭐⭐⭐ Good | ⭐⭐⭐ Good |

## Troubleshooting

### "LLM provider requires [PROVIDER]_API_KEY to be set"

- Ensure you've set the correct API key for your chosen provider
- Check that the key is valid and not expired
- Verify the key has appropriate permissions/credits

### "Unsupported LLM provider"

- Valid providers: `openai`, `openrouter`, `deepseek`, `gemini`
- Check `LLM_PROVIDER` spelling in `.env`
- Restart backend after changing provider

### JSON Parsing Failures

Some models are less reliable at producing valid JSON. If you experience frequent parsing errors:

1. **Switch to a more reliable model** (GPT-4o, Claude 3.5)
2. **Increase temperature** slightly (0.1-0.3) for more creative JSON
3. **Check agent prompts** - ensure they clearly request JSON output

### Rate Limiting

If you hit rate limits:

1. **Upgrade your API tier** with the provider
2. **Switch to a different provider** as a fallback
3. **Implement caching** for frequently analyzed routes
4. **Add delays** between analyses

## Recommendations

### For Production

**Best balance of cost and quality:**
- Primary: OpenAI GPT-4o
- Fallback: OpenRouter Claude 3.5 Sonnet

**Most cost-effective:**
- Primary: DeepSeek Chat or Gemini 1.5 Flash
- Fallback: OpenRouter Llama 3.1 70B

### For Development/Testing

Use cheaper models to avoid high costs during development:
- DeepSeek Chat ($0.004 per analysis)
- Gemini 1.5 Flash ($0.004 per analysis)
- OpenAI GPT-3.5 Turbo ($0.02 per analysis)

### For Maximum Quality

When accuracy is critical:
- OpenAI GPT-4o ($0.10 per analysis)
- OpenRouter Claude 3.5 Sonnet ($0.15 per analysis)

## Switching Providers

To switch providers, simply update your `.env` and restart the backend:

```bash
# Switch from OpenAI to DeepSeek
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# Restart
./run_dev.sh
```

The frontend will automatically detect the active provider through the `/api/agentic/status` endpoint.

## Next Steps

1. **Choose your provider** based on cost and quality needs
2. **Get an API key** from the provider's website
3. **Configure `.env`** with your provider and key
4. **Test with a single analysis** to verify configuration
5. **Monitor costs** in your provider dashboard
6. **Optimize** by caching results or switching models

For more details, see [AGENTIC_INTEGRATION.md](./AGENTIC_INTEGRATION.md).
