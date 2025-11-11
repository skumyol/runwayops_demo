from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class FlightMonitorProvider(ABC):
    """Abstract base class every provider must implement."""

    mode: str

    @abstractmethod
    async def get_payload(self, airport: str, carrier: str) -> Dict[str, Any]:
        """Fetch and shape monitor data."""
        raise NotImplementedError
