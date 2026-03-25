from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from courtney.agents.abstract.base_llm import call_llm, LLMResponse
from courtney.agents.landrecord.schemas.extraction import LandRecordExtraction
from courtney.models import Agent

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    extraction: LandRecordExtraction
    tokens_input: int
    tokens_output: int


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.lstrip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.rstrip("`").strip()
    return stripped


async def extract_structured_data(
    raw_text: str,
    client: httpx.AsyncClient,
    agent: Agent,
) -> ExtractionResult:
    """
    Extracts structured land record fields from raw_text using the given agent.
    Returns an ExtractionResult with a validated LandRecordExtraction and token counts.
    Falls back to an empty LandRecordExtraction on JSON parse failure.
    """
    schema_hint = f"\n\nJSON Schema to follow:\n{json.dumps(LandRecordExtraction.model_json_schema(), indent=2)}"
    system_prompt = agent.system_prompt + schema_hint

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_text},
    ]

    response: LLMResponse = await call_llm(client, agent.model, messages)
    raw_content = _strip_markdown_fences(response.content)

    try:
        extraction = LandRecordExtraction.model_validate_json(raw_content)
    except Exception:
        try:
            extraction = LandRecordExtraction.model_validate(json.loads(raw_content))
        except Exception:
            logger.warning("Extraction agent returned unparseable content; returning empty extraction")
            extraction = LandRecordExtraction()

    return ExtractionResult(
        extraction=extraction,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
    )
