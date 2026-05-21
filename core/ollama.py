from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx
from django.conf import settings

from .langfuse import start_generation


logger = logging.getLogger(__name__)


MAX_RETRIES = 3


@dataclass
class LLMResponse:
    content: str


async def call_llm(
        client: httpx.AsyncClient,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.0
    ) -> LLMResponse:

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": settings.OLLAMA_NUM_CTX,
        },
    }

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with start_generation(
                name=f"ollama-{model}",
                model=model,
                input=messages,
                model_parameters={"temperature": temperature, "num_ctx": settings.OLLAMA_NUM_CTX},
                metadata={"attempt": attempt},
            ) as gen:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                    timeout=settings.OLLAMA_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                content = data.get("message", {}).get("content", "")
            
                if gen is not None:
                    gen.update(
                        output=content,
                        usage_details={
                            "input": data.get("prompt_eval_count", 0),
                            "output": data.get("eval_count", 0),
                        },
                        metadata={
                            "attempt": attempt,
                            "done_reason": data.get("done_reason"),
                            "total_duration_ms": data.get("total_duration", 0) / 1_000_000,
                            "load_duration_ms": data.get("load_duration", 0) / 1_000_000,
                            "prompt_eval_duration_ms": data.get("prompt_eval_duration", 0) / 1_000_000,
                            "eval_duration_ms": data.get("eval_duration", 0) / 1_000_000,
                        },
                    )

            return LLMResponse(content=content)

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning("LLM call attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)

        except (httpx.HTTPStatusError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"LLM call non-retryable error: {exc}") from exc

    raise RuntimeError(f"LLM call failed after {MAX_RETRIES} retries: {last_exc}")
