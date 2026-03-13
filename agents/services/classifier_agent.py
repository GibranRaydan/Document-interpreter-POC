import json
import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

VALID_DOC_TYPES = {"invoice", "receipt", "contract", "form", "other"}

SYSTEM_PROMPT = (
    "You are a document classifier. Given the text of a document, "
    "classify it into exactly one of these categories: "
    "invoice, receipt, contract, form, other. "
    "Respond with ONLY the category name in lowercase. "
    "Do not include any other text, punctuation, or explanation."
)

MAX_RETRIES = 3


async def classify_document(raw_text: str, client: httpx.AsyncClient) -> str:
    """
    Classifies the document text into one of the supported doc_type values.
    Returns a string from VALID_DOC_TYPES. Defaults to 'other' if the model
    returns an unexpected value.
    """
    payload = {
        "model": settings.OLLAMA_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text[:3000]},  # Truncate to avoid context overflow
        ],
        "stream": False,
        "options": {"temperature": 0.0},
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
            raw_label = data["message"]["content"].strip().lower()
            if raw_label in VALID_DOC_TYPES:
                return raw_label
            logger.warning(
                "Classifier returned unexpected label %r, defaulting to 'other'",
                raw_label,
            )
            return "other"

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning(
                "Classifier agent connection error on attempt %d/%d: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
        except (httpx.HTTPStatusError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Classifier agent failed with non-retryable error: {exc}"
            ) from exc

    raise RuntimeError(
        f"Classifier agent failed after {MAX_RETRIES} retries: {last_exc}"
    )
