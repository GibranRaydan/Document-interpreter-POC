from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from django.conf import settings

from courtney_async.agents.abstract.langfuse_client import start_generation

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class LLMResponse:
    def __init__(self, content: str, tokens_input: int, tokens_output: int):
        self.content = content
        self.tokens_input = tokens_input
        self.tokens_output = tokens_output


async def call_llm(
    client: httpx.AsyncClient,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.0,
) -> LLMResponse:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=settings.OLLAMA_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            content = data["message"]["content"]
            tokens_input = data.get("prompt_eval_count", 0)
            tokens_output = data.get("eval_count", 0)

            try:
                with start_generation(
                    name=f"ollama-{model}",
                    model=model,
                    input=messages,
                    model_parameters={"temperature": temperature},
                    metadata={"attempt": attempt},
                ) as gen:
                    gen.update(
                        output=content,
                        usage_details={"input": tokens_input, "output": tokens_output},
                    )
            except Exception:
                logger.debug("Langfuse generation logging failed", exc_info=True)

            return LLMResponse(content=content, tokens_input=tokens_input, tokens_output=tokens_output)

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning("LLM call attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)

        except (httpx.HTTPStatusError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"LLM call non-retryable error: {exc}") from exc

    raise RuntimeError(f"LLM call failed after {MAX_RETRIES} retries: {last_exc}")
