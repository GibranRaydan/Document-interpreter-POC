from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import httpx
import pytesseract
from pdf2image import convert_from_bytes

from courtney.agents.abstract.base_llm import call_llm, LLMResponse
from courtney.models import Agent

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    raw_text: str
    tokens_input: int
    tokens_output: int


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Converts a PDF into images and extracts text using Tesseract OCR.
    """
    images = convert_from_bytes(pdf_bytes, dpi=300)

    full_text = []
    for i, image in enumerate(images):
        try:
            text = pytesseract.image_to_string(image, lang="eng")
            full_text.append(text)
        except Exception:
            logger.exception(f"OCR failed on page {i}")

    return "\n".join(full_text)


async def extract_text(file_path: str, client: httpx.AsyncClient, agent: Agent) -> OCRResult:
    """
    Reads the image at `file_path`, encodes it as base64, and sends it to the
    vision model defined in `agent`.

    Returns an OCRResult with the extracted text and token counts.
    Raises ValueError for unsupported file types, RuntimeError on LLM failure.
    """
    # if file_path.lower().endswith(".pdf"):
    #     raise ValueError("PDF OCR not yet implemented. Please upload an image.")

    # with open(file_path, "rb") as f:
    #     file_b64 = base64.b64encode(f.read()).decode("utf-8")

    # messages = [
    #     {
    #         "role": "user",
    #         "content": agent.system_prompt,
    #         "images": [file_b64],
    #     }
    # ]

    # response: LLMResponse = await call_llm(client, agent.model, messages)

    # return OCRResult(
    #     raw_text=response.content,
    #     tokens_input=response.tokens_input,
    #     tokens_output=response.tokens_output,
    # )

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
        extracted_text = extract_text_from_pdf(pdf_bytes)

    return OCRResult(
        raw_text=extracted_text,
        tokens_input=0,
        tokens_output=0,
    )
