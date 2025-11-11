from __future__ import annotations

from functools import lru_cache
from typing import Literal

from ..config import settings
from ..exceptions import ProviderConfigError
from .base import FlightMonitorProvider
from .mongo_stream import MongoMonitorProvider
from .realtime import AviationStackMonitorProvider
from .synthetic import SyntheticMonitorProvider

ProviderMode = Literal["synthetic", "realtime", "mongo"]


@lru_cache(maxsize=4)
def _synthetic_provider() -> FlightMonitorProvider:
    return SyntheticMonitorProvider()


def _realtime_provider() -> FlightMonitorProvider:
    return AviationStackMonitorProvider(
        api_key=settings.aviationstack_api_key,
        base_url=settings.aviationstack_base_url,
    )


@lru_cache(maxsize=4)
def _mongo_provider() -> FlightMonitorProvider:
    return MongoMonitorProvider()


def resolve_provider(mode: ProviderMode | None = None) -> FlightMonitorProvider:
    selected_mode = (mode or settings.default_mode).lower()
    if selected_mode == "realtime":
        return _realtime_provider()
    if selected_mode == "synthetic":
        return _synthetic_provider()
    if selected_mode == "mongo":
        return _mongo_provider()
    raise ProviderConfigError(f"Unsupported provider mode: {selected_mode}")
