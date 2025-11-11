from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient

from ..config import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
