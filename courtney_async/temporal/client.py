from __future__ import annotations

from temporalio.client import Client

from .config import temporal_address, temporal_namespace

_client: Client | None = None


async def get_temporal_client() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect(temporal_address(), namespace=temporal_namespace())
    return _client
