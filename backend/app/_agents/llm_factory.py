"""LLM provider factory for multi-provider support.

Supports:
- OpenAI (native)
- OpenRouter (OpenAI-compatible API)
- DeepSeek (OpenAI-compatible API)
- Google Gemini (native)
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ..config import settings


class LLMProviderError(Exception):
    """Raised when LLM provider configuration is invalid."""
    pass


def get_llm(provider_override: str | None = None) -> BaseChatModel:
    """Get configured LLM instance based on provider settings.
    
    Args:
        provider_override: Optional provider name to use instead of settings.llm_provider
        
    Returns:
        Configured LangChain chat model instance
        
    Raises:
        LLMProviderError: If provider is not configured or unsupported
    """
    provider = (provider_override or settings.llm_provider).lower()
    
    if provider == "openai":
        return _get_openai_llm()
    elif provider == "openrouter":
        return _get_openrouter_llm()
    elif provider == "deepseek":
        return _get_deepseek_llm()
    elif provider == "gemini":
        return _get_gemini_llm()
    else:
        raise LLMProviderError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported: openai, openrouter, deepseek, gemini"
        )


def _get_openai_llm() -> ChatOpenAI:
    """Get OpenAI LLM instance."""
    if not settings.openai_api_key:
        raise LLMProviderError(
            "OpenAI provider requires OPENAI_API_KEY to be set"
        )
    
    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "api_key": settings.openai_api_key,
    }
    
    # Support custom OpenAI-compatible endpoints
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    
    return ChatOpenAI(**kwargs)


def _get_openrouter_llm() -> ChatOpenAI:
    """Get OpenRouter LLM instance (OpenAI-compatible API).
    
    OpenRouter supports multiple models through an OpenAI-compatible interface.
    Example models:
    - anthropic/claude-3.5-sonnet
    - google/gemini-pro-1.5
    - meta-llama/llama-3.1-70b-instruct
    """
    if not settings.openrouter_api_key:
        raise LLMProviderError(
            "OpenRouter provider requires OPENROUTER_API_KEY to be set"
        )
    
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_headers={
            "HTTP-Referer": "https://github.com/runwayops",  # Optional: for rankings
            "X-Title": "Runway Ops Flight Monitor",
        },
    )


def _get_deepseek_llm() -> ChatOpenAI:
    """Get DeepSeek LLM instance (OpenAI-compatible API).
    
    DeepSeek provides OpenAI-compatible API.
    Example models:
    - deepseek-chat
    - deepseek-coder
    """
    if not settings.deepseek_api_key:
        raise LLMProviderError(
            "DeepSeek provider requires DEEPSEEK_API_KEY to be set"
        )
    
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


def _get_gemini_llm() -> BaseChatModel:
    """Get Google Gemini LLM instance.
    
    Example models:
    - gemini-pro
    - gemini-1.5-pro
    - gemini-1.5-flash
    """
    if not settings.gemini_api_key:
        raise LLMProviderError(
            "Gemini provider requires GEMINI_API_KEY to be set"
        )
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as e:
        raise LLMProviderError(
            "langchain-google-genai package not installed. "
            "Run: uv pip install langchain-google-genai"
        ) from e
    
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        google_api_key=settings.gemini_api_key,
    )


def get_provider_info() -> dict[str, Any]:
    """Get information about configured LLM provider.
    
    Returns:
        Dictionary with provider details and configuration status
    """
    provider = settings.llm_provider
    
    # Check which providers are configured
    providers_status = {
        "openai": {
            "configured": bool(settings.openai_api_key),
            "endpoint": settings.openai_base_url or "https://api.openai.com/v1",
            "example_models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        },
        "openrouter": {
            "configured": bool(settings.openrouter_api_key),
            "endpoint": settings.openrouter_base_url,
            "example_models": [
                "anthropic/claude-3.5-sonnet",
                "google/gemini-pro-1.5",
                "meta-llama/llama-3.1-70b-instruct",
            ],
        },
        "deepseek": {
            "configured": bool(settings.deepseek_api_key),
            "endpoint": settings.deepseek_base_url,
            "example_models": ["deepseek-chat", "deepseek-coder"],
        },
        "gemini": {
            "configured": bool(settings.gemini_api_key),
            "endpoint": "Google AI Studio",
            "example_models": ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
        },
    }
    
    return {
        "current_provider": provider,
        "current_model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "providers": providers_status,
        "provider_configured": providers_status[provider]["configured"],
    }
