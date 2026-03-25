"""Singleton Langfuse client for the entire Django process."""

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
    """Start a new observation as the current trace root (context manager)."""
    return get_langfuse().start_as_current_observation(
        name=name, as_type="span", **kwargs
    )


def start_span(name: str, **kwargs):
    """Start a child span under the current observation (context manager)."""
    lf = get_langfuse()
    return lf.start_as_current_observation(
        name=name, as_type="span", **kwargs
    )


def start_generation(name: str, **kwargs):
    """Start a generation under the current observation (context manager)."""
    lf = get_langfuse()
    return lf.start_as_current_observation(
        name=name, as_type="generation", **kwargs
    )
