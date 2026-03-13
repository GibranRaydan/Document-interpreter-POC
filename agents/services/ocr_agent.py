import base64
import json
import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

# TODO: NLP, procesamiento de lenguaje natural SKLearn

SYSTEM_PROMPT = (
    "You are an OCR engine. Extract ALL visible text from the provided image. "
    "Return only the extracted text with no additional commentary, formatting, "
    "or explanation. Preserve line breaks as they appear in the image."
)

MAX_RETRIES = 3


async def extract_text(file_path: str, client: httpx.AsyncClient) -> str:
    """
    Reads the file at `file_path`, detects type, and processes it.
    For images: encodes as base64 and sends to vision model.
    For PDFs: currently raises ValueError (placeholder for future implementation).

    Raises RuntimeError if all retries fail or file type is unsupported.
    """
    # Detect file type by extension
    if file_path.lower().endswith(".pdf"):
        raise ValueError("PDF OCR not yet implemented. Please upload an image.")

    # Read and encode image file
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_b64 = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "model": settings.OLLAMA_VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": SYSTEM_PROMPT,
                "images": [file_b64],
            }
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
            return data["message"]["content"]

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning(
                "OCR agent connection error on attempt %d/%d: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
        except (httpx.HTTPStatusError, KeyError, json.JSONDecodeError) as exc:
            # Non-retryable errors: bad response, missing key, bad JSON
            raise RuntimeError(
                f"OCR agent failed with non-retryable error: {exc}"
            ) from exc

    raise RuntimeError(f"OCR agent failed after {MAX_RETRIES} retries: {last_exc}")
