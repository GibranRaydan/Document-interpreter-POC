import json
import logging

import httpx
from django.conf import settings

from agents.schemas.document_schemas import SCHEMAS_MAP

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

SYSTEM_PROMPT_TEMPLATE = (
    "You are a structured data extraction engine. "
    "Given the text of a {doc_type}, extract all relevant fields "
    "and return ONLY a valid JSON object matching the provided schema. "
    "Do not include any explanation or markdown. Return raw JSON only."
)


async def extract_structured_data(
    raw_text: str,
    doc_type: str,
    client: httpx.AsyncClient,
) -> dict:
    """
    Extracts structured data from raw_text for the given doc_type.
    Returns a dict. If doc_type has no schema or extraction fails,
    returns a best-effort dict or an empty dict.
    """
    schema_class = SCHEMAS_MAP.get(doc_type)
    schema_hint = ""
    if schema_class:
        schema_hint = f"\n\nJSON Schema to follow:\n{json.dumps(schema_class.model_json_schema(), indent=2)}"

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(doc_type=doc_type) + schema_hint

    payload = {
        "model": settings.OLLAMA_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text[:6000]},
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
            raw_content = data["message"]["content"]

            # Strip markdown fences if model wraps in ```json ... ```
            if raw_content.strip().startswith("```"):
                raw_content = raw_content.strip().lstrip("`")
                if raw_content.lower().startswith("json"):
                    raw_content = raw_content[4:]
                raw_content = raw_content.rstrip("`").strip()

            return json.loads(raw_content)

        except json.JSONDecodeError:
            logger.warning(
                "Extraction agent returned non-JSON, returning raw string wrapper"
            )
            return {"raw_content": raw_content}  # type: ignore[possibly-undefined]
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning(
                "Extraction agent connection error on attempt %d/%d: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
        except (httpx.HTTPStatusError, KeyError) as exc:
            raise RuntimeError(
                f"Extraction agent failed with non-retryable error: {exc}"
            ) from exc

    raise RuntimeError(
        f"Extraction agent failed after {MAX_RETRIES} retries: {last_exc}"
    )
