from __future__ import annotations

import logging
import uuid
from contextlib import nullcontext

from django.conf import settings

from langfuse import Langfuse


logger = logging.getLogger(__name__)


_client: Langfuse | None = None


def get_langfuse() -> Langfuse:
    """Returns a singleton Langfuse client instance. Safe to call — never raises."""
    global _client
    if _client is None:
        _client = Langfuse(
            secret_key=settings.LANGFUSE_SECRET_KEY,
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
    return _client


def start_trace(name: str, **kwargs) -> str:
    """Creates a Langfuse trace and returns its ID. Safe to call — never raises."""
    trace_id = uuid.uuid4().hex
    try:
        get_langfuse().trace(
            id=trace_id,
            name=name,
            **kwargs
        )
    except Exception:
        logger.error("Langfuse trace creation failed", exc_info=True)
    return trace_id


def start_span_in_trace(trace_id: str, name: str, **kwargs):
    """Starts a span in the given trace. Safe to call — never raises."""
    try:
        return get_langfuse().start_as_current_observation(
            name=name,
            as_type="span",
            trace_context={"trace_id": trace_id},
            **kwargs,
        )
    except Exception:
        logger.error("Langfuse span init failed", exc_info=True)
        return nullcontext()


def start_generation(name: str, **kwargs):
    """Starts a generation observation. Safe to call — never raises."""
    try:
        return get_langfuse().start_as_current_observation(
            name=name, as_type="generation", **kwargs
        )
    except Exception:
        logger.error("Langfuse generation init failed", exc_info=True)
        return nullcontext()
