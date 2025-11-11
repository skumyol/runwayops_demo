class ProviderError(Exception):
    """Base error for flight monitor providers."""


class ProviderConfigError(ProviderError):
    """Provider is misconfigured (e.g., missing API keys)."""


class ProviderDataError(ProviderError):
    """Provider could not return sane data."""
