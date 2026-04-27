from __future__ import annotations

import base64
import io
import logging

import httpx
from pdf2image import convert_from_bytes
from PIL import Image

from core.ollama import call_llm, LLMResponse


logger = logging.getLogger(__name__)


TESSERACT_URL = "http://localhost:3001"
WITH_TESSERACT = True

OCR_PROMPT = (
    "You are an OCR engine. Extract ALL visible text from the provided image. "
    "Return only the extracted text with no additional commentary, formatting, "
    "or explanation. Preserve line breaks as they appear in the image."
)

MIME_TYPES = {
    "pdf": "image/png",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "tiff": "image/tiff",
    "tif": "image/tiff",
}

CONVERT_BYTES_MAP = {
    "pdf": lambda raw: _pdf_to_page_bytes(raw),
}

CONVERT_B64_MAP = {
    "pdf": lambda raw: _pdf_to_base64_images(raw),
    "tiff": lambda raw: _tiff_to_base64(raw),
    "tif": lambda raw: _tiff_to_base64(raw),
}


def _mime_type_and_filename(extension: str) -> tuple[str, str]:
    extension = extension.lower()
    mime_type = MIME_TYPES.get(extension, "application/octet-stream")
    filename = f"file.{extension}"
    return mime_type, filename


def _open_raw_file(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return f.read()


def _convert_to_bytes(raw: bytes, extension: str) -> list[bytes]:
    converter = CONVERT_BYTES_MAP.get(extension.lower(), lambda r: [r])
    return converter(raw)


def _convert_to_base64_images(raw: bytes, extension: str) -> list[str]:
    converter = CONVERT_B64_MAP.get(extension.lower(), lambda r: [base64.b64encode(r).decode("utf-8")])
    return converter(raw)


def _tiff_to_base64(tiff_bytes: bytes) -> list[str]:
    return [base64.b64encode(page).decode("utf-8") for page in _tiff_to_bytes(tiff_bytes)]


def _tiff_to_bytes(tiff_bytes: bytes) -> list[bytes]:
    img = Image.open(io.BytesIO(tiff_bytes))
    result = []
    for i in range(getattr(img, "n_frames", 1)):
        img.seek(i)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result.append(buf.getvalue())
    return result


def _pdf_to_base64_images(pdf_bytes: bytes) -> list[str]:
    return [base64.b64encode(page).decode("utf-8") for page in _pdf_to_page_bytes(pdf_bytes)]


def _pdf_to_page_bytes(pdf_bytes: bytes) -> list[bytes]:
    pages = convert_from_bytes(pdf_bytes, dpi=300)
    result = []
    for page in pages:
        buf = io.BytesIO()
        page.save(buf, format="PNG")
        result.append(buf.getvalue())
    return result


async def extract_with_llm(file_path: str, client: httpx.AsyncClient) -> str:
    logger.debug(f"Starting LLM OCR for file: {file_path}")
    raw_file = _open_raw_file(file_path)
    extension = file_path.lower().split(".")[-1]
    images_b64 = _convert_to_base64_images(raw_file, extension)

    messages = [
        {"role": "system", "content": OCR_PROMPT},
        {
            "role": "user",
            "content": "Extract the text from the provided image(s).",
            "images": images_b64,
        },
    ]
    response: LLMResponse = await call_llm(client, "minicpm-v", messages)
    logger.debug("LLM OCR completed.")
    return response.content


async def extract_with_tesseract(file_path: str, client: httpx.AsyncClient) -> str:
    logger.debug(f"Starting Tesseract OCR for file: {file_path}")
    raw_file = _open_raw_file(file_path)
    extension = file_path.lower().split(".")[-1]
    file_bytes = _convert_to_bytes(raw_file, extension)
    mime_type, filename = _mime_type_and_filename(extension)
    texts: list[str] = []
    for page_bytes in file_bytes:
        response = await client.post(
            f"{TESSERACT_URL}/tesseract",
            files={"file": (filename, page_bytes, mime_type)},
            data={"options": "{}"},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        texts.append(data.get("data", {}).get("stdout", ""))
    logger.debug(f"Tesseract OCR completed. Pages processed: {len(texts)}.")
    return "\n".join(texts)
