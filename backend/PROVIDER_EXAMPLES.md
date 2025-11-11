# LLM Provider Configuration Examples

Quick copy-paste configurations for each supported provider.

## OpenAI (GPT-4o)

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.2
OPENAI_API_KEY=sk-proj-xxxxx
```

**Get API key**: https://platform.openai.com/api-keys

## OpenRouter (Claude 3.5 Sonnet)

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.2
OPENROUTER_API_KEY=sk-or-xxxxx
```

**Get API key**: https://openrouter.ai/keys  
**Model list**: https://openrouter.ai/models

### Other OpenRouter Models

```bash
# Gemini Pro via OpenRouter
LLM_MODEL=google/gemini-pro-1.5

# Llama 3.1 70B (cost-effective)
LLM_MODEL=meta-llama/llama-3.1-70b-instruct

# GPT-4o via OpenRouter
LLM_MODEL=openai/gpt-4o
```

## DeepSeek (Chat)

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2
DEEPSEEK_API_KEY=sk-xxxxx
```

**Get API key**: https://platform.deepseek.com/  
**Pricing**: $0.14/1M input tokens, $0.28/1M output tokens

## Google Gemini (1.5 Pro)

```bash
# backend/.env
AGENTIC_ENABLED=true
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-pro
LLM_TEMPERATURE=0.2
GEMINI_API_KEY=AIzaSyXXXXX
```

**Get API key**: https://makersuite.google.com/app/apikey

### Other Gemini Models

```bash
# Fastest and cheapest
LLM_MODEL=gemini-1.5-flash

# Previous generation (still good)
LLM_MODEL=gemini-pro
```

## Testing Configuration

Verify your configuration with curl:

```bash
# Check provider status
curl http://localhost:8000/api/agentic/status | jq

# Get detailed provider info
curl http://localhost:8000/api/agentic/providers | jq
```

Expected output when configured:
```json
{
  "enabled": true,
  "current_provider": "openai",
  "current_model": "gpt-4o",
  "temperature": 0.2,
  "provider_configured": true,
  "providers": {
    "openai": {
      "configured": true,
      ...
    }
  }
}
```

## Switching Providers

1. Update `.env` with new provider configuration
2. Restart backend: `./run_dev.sh`
3. Verify in dashboard or via API

No code changes needed - the system automatically uses the configured provider!
