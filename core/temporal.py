from __future__ import annotations

import asyncio
import logging

from datetime import timedelta

from django.conf import settings

from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio import activity


logger = logging.getLogger(__name__)


_client: Client | None = None


async def get_temporal() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect(temporal_address(), namespace=temporal_namespace())
    return _client


def temporal_address() -> str:
    return getattr(settings, "TEMPORAL_ADDRESS", "localhost:7233")


def temporal_namespace() -> str:
    return getattr(settings, "TEMPORAL_NAMESPACE", "default")


def temporal_task_queue() -> str:
    return getattr(settings, "TEMPORAL_TASK_QUEUE", "courtney-landrecord")


def temporal_ocr_task_queue() -> str:
    return getattr(settings, "TEMPORAL_OCR_TASK_QUEUE", "courtney-landrecord-ocr")


def ocr_max_concurrent() -> int:
    return getattr(settings, "OCR_MAX_CONCURRENT_ACTIVITIES", 3)


DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
    non_retryable_error_types=["ValueError"],
)


def create_heartbeat_task(interval: int = 10) -> asyncio.Task:
    async def _heartbeat_loop():
        while True:
            await asyncio.sleep(interval)
            activity.heartbeat()
    return asyncio.create_task(_heartbeat_loop())
