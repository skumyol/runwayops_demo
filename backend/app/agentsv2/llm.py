"""Lightweight LLM helper used by the ADK agents.

This mirrors the behavior from the legacy LangGraph implementation but keeps
the dependency surface local to agentsv2 so the package can be imported
without pulling in the archived modules under `#__agents`.
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ..config import settings


class LLMProviderError(RuntimeError):
    """Raised when the configured provider cannot be instantiated."""


def get_llm(provider_override: str | None = None) -> BaseChatModel:
    """Return a LangChain-compatible chat model for the configured provider."""
    provider = (provider_override or settings.llm_provider).lower()

    if provider == "openai":
        return _build_openai_llm()
    if provider == "openrouter":
        return _build_openrouter_llm()
    if provider == "deepseek":
        return _build_deepseek_llm()
    if provider == "gemini":
        return _build_gemini_llm()

    raise LLMProviderError(
        f"Unsupported LLM provider '{provider}'. "
        "Supported providers: openai, openrouter, deepseek, gemini."
    )


def _build_openai_llm() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise LLMProviderError(
            "OPENAI_API_KEY must be set when LLM_PROVIDER=openai."
        )

    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "api_key": settings.openai_api_key,
    }

    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url

    return ChatOpenAI(**kwargs)


def _build_openrouter_llm() -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise LLMProviderError(
            "OPENROUTER_API_KEY must be set when LLM_PROVIDER=openrouter."
        )

    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_headers={
            "HTTP-Referer": "https://github.com/runwayops",
            "X-Title": "Runway Ops Flight Monitor",
        },
    )


def _build_deepseek_llm() -> ChatOpenAI:
    if not settings.deepseek_api_key:
        raise LLMProviderError(
            "DEEPSEEK_API_KEY must be set when LLM_PROVIDER=deepseek."
        )

    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


def _build_gemini_llm() -> BaseChatModel:
    if not settings.gemini_api_key:
        raise LLMProviderError(
            "GEMINI_API_KEY must be set when LLM_PROVIDER=gemini."
        )

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:  # pragma: no cover - import guard
        raise LLMProviderError(
            "langchain-google-genai is required for Gemini. "
            "Install via `uv pip install langchain-google-genai`."
        ) from exc

    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        google_api_key=settings.gemini_api_key,
    )


__all__ = ["get_llm", "LLMProviderError"]
