from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass

import httpx
from pdf2image import convert_from_bytes

from courtney.agents.abstract.base_llm import call_llm, LLMResponse
from courtney.models import Agent

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    raw_text: str
    tokens_input: int
    tokens_output: int


def _pdf_to_base64_images(pdf_bytes: bytes) -> list[str]:
    """Convert a PDF to a list of base64-encoded PNG images (one per page)."""
    pages = convert_from_bytes(pdf_bytes, dpi=300)
    images_b64 = []
    for page in pages:
        buf = io.BytesIO()
        page.save(buf, format="PNG")
        images_b64.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
    return images_b64


async def extract_text(file_path: str, client: httpx.AsyncClient, agent: Agent) -> OCRResult:
    """
    Reads the file at `file_path`, encodes it as base64, and sends it to the
    vision model defined in `agent`.  Supports images and PDFs (multi-page).

    Returns an OCRResult with the extracted text and token counts.
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    if file_path.lower().endswith(".pdf"):
        images_b64 = _pdf_to_base64_images(raw)
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
