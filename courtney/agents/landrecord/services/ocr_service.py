from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass

import httpx
from pdf2image import convert_from_bytes
from PIL import Image

from courtney.agents.abstract.base_llm import call_llm, LLMResponse
from courtney.models import Agent

logger = logging.getLogger(__name__)

WITH_TESSERACT = True

TESSERACT_URL = "http://localhost:3001"


@dataclass
class OCRResult:
    raw_text: str
    tokens_input: int
    tokens_output: int


def _tiff_to_page_bytes(tiff_bytes: bytes) -> list[bytes]:
    """Convert a multi-page TIFF to a list of PNG bytes (one per page)."""
    img = Image.open(io.BytesIO(tiff_bytes))
    result = []
    for i in range(getattr(img, "n_frames", 1)):
        img.seek(i)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result.append(buf.getvalue())
    return result


def _tiff_to_base64_images(tiff_bytes: bytes) -> list[str]:
    """Convert a multi-page TIFF to a list of base64-encoded PNG images."""
    return [base64.b64encode(page).decode("utf-8") for page in _tiff_to_page_bytes(tiff_bytes)]


def _pdf_to_base64_images(pdf_bytes: bytes) -> list[str]:
    """Convert a PDF to a list of base64-encoded PNG images (one per page)."""
    pages = convert_from_bytes(pdf_bytes, dpi=300)
    images_b64 = []
    for page in pages:
        buf = io.BytesIO()
        page.save(buf, format="PNG")
        images_b64.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
    return images_b64


def _pdf_to_page_bytes(pdf_bytes: bytes) -> list[bytes]:
    """Convert a PDF to a list of PNG bytes (one per page)."""
    pages = convert_from_bytes(pdf_bytes, dpi=300)
    result = []
    for page in pages:
        buf = io.BytesIO()
        page.save(buf, format="PNG")
        result.append(buf.getvalue())
    return result


async def _tesseract_extract(file_path: str, client: httpx.AsyncClient) -> str:
    """Send image/PDF pages to the Tesseract HTTP service and return extracted text."""
    with open(file_path, "rb") as f:
        raw = f.read()

    if file_path.lower().endswith(".pdf"):
        pages_bytes = _pdf_to_page_bytes(raw)
    elif file_path.lower().endswith((".tiff", ".tif")):
        pages_bytes = _tiff_to_page_bytes(raw)
    else:
        pages_bytes = [raw]

    texts: list[str] = []
    for page_bytes in pages_bytes:
        response = await client.post(
            f"{TESSERACT_URL}/tesseract",
            files={"file": ("page.png", page_bytes, "image/png")},
            data={"options": "{}"},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        texts.append(data.get("data", {}).get("stdout", ""))

    return "\n".join(texts)


async def extract_text(file_path: str, client: httpx.AsyncClient, agent: Agent) -> OCRResult:
    """
    Reads the file at `file_path` and extracts text.

    If WITH_TESSERACT is True, sends pages to the Tesseract Docker service (no LLM tokens used).
    Otherwise, encodes as base64 and sends to the vision LLM defined in `agent`.

    Returns an OCRResult with the extracted text and token counts.
    """
    if WITH_TESSERACT:
        logger.info("OCR via Tesseract service for %s", file_path)
        raw_text = await _tesseract_extract(file_path, client)
        return OCRResult(raw_text=raw_text, tokens_input=0, tokens_output=0)

    with open(file_path, "rb") as f:
        raw = f.read()

    if file_path.lower().endswith(".pdf"):
        images_b64 = _pdf_to_base64_images(raw)
    elif file_path.lower().endswith((".tiff", ".tif")):
        images_b64 = _tiff_to_base64_images(raw)
    else:
        images_b64 = [base64.b64encode(raw).decode("utf-8")]

    messages = [
        {
            "role": "user",
            "content": agent.system_prompt,
            "images": images_b64,
        }
    ]

    response: LLMResponse = await call_llm(client, agent.model, messages)

    return OCRResult(
        raw_text=response.content,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
    )
