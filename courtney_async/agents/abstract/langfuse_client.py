"""Singleton Langfuse client for courtney_async."""

from __future__ import annotations

from langfuse import Langfuse
from django.conf import settings

_client: Langfuse | None = None


def get_langfuse() -> Langfuse:
    global _client
    if _client is None:
        _client = Langfuse(
            secret_key=settings.LANGFUSE_SECRET_KEY,
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
    return _client


def start_trace(name: str, **kwargs):
    return get_langfuse().start_as_current_observation(
        name=name, as_type="span", **kwargs
    )


def start_span(name: str, **kwargs):
    return get_langfuse().start_as_current_observation(
        name=name, as_type="span", **kwargs
    )


def start_generation(name: str, **kwargs):
    return get_langfuse().start_as_current_observation(
        name=name, as_type="generation", **kwargs
    )


def start_span_in_trace(trace_id: str, name: str, **kwargs):
    """Open a child span under an existing trace identified by trace_id."""
    lf = get_langfuse()
    return lf.start_as_current_observation(
        name=name,
        as_type="span",
        trace_context={"trace_id": trace_id},
        **kwargs,
    )
