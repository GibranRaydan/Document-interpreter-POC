from __future__ import annotations

import json
import logging

import httpx

from temporalio import activity

from core.langfuse import start_span_in_trace
from core.ollama import call_llm, LLMResponse
from core.temporal import create_heartbeat_task

from courtney.models import Page
from ..ctx import TraceContext, RecordContext, ExtractContext
from ..schemas import LandRecordExtraction


logger = logging.getLogger(__name__)


@activity.defn
async def extract_activity(record_ctx: RecordContext, trace_ctx: TraceContext) -> ExtractContext:
    raw_text_parts = []
    async for page in Page.objects.filter(record_id=record_ctx.pk).order_by("id"):
        if page.raw_text:
            raw_text_parts.append(page.raw_text)
    combined_text = "\n\n".join(raw_text_parts)

    heartbeat_task = create_heartbeat_task(interval=10)
    try:
        async with httpx.AsyncClient() as client:
            with start_span_in_trace(trace_ctx.id, name="extract"):
                extraction = await extract_structured_data(combined_text, client)
                result = ExtractContext(record_pk=record_ctx.pk, extraction=extraction.model_dump())
    except Exception:
        raise
    finally:
        heartbeat_task.cancel()

    return result


async def extract_structured_data(raw_text: str, client: httpx.AsyncClient) -> LandRecordExtraction:
    logger.debug("Starting LLM Extract structured data")
    schema_hint = f"\n\nJSON Schema to follow:\n{json.dumps(LandRecordExtraction.model_json_schema(), indent=2)}"
    system_prompt = EXTRACTOR_PROMPT + schema_hint

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_text},
    ]
    response: LLMResponse = await call_llm(client, "llama3.1", messages)
    logger.debug("LLM Extract completed.")

    raw_content = _strip_markdown_fences(response.content)
    try:
        return LandRecordExtraction.model_validate_json(raw_content)
    except Exception:
        try:
            return LandRecordExtraction.model_validate(json.loads(raw_content))
        except Exception:
            logger.warning("Extraction agent returned unparseable content; returning empty extraction")
            raise


EXTRACTOR_PROMPT = (
    "You are a structured data extraction engine for land record documents. "
    "Extract all relevant fields and return ONLY a valid JSON object. "
    "Do not include any explanation or markdown. Return raw JSON only.\n\n"
    "IMPORTANT RULES FOR PARTIES:\n"
    "- Separate parties into two lists: individual_parties (people) and firm_parties (companies, banks, entities).\n"
    "- The only valid party_type values are GRANTOR and GRANTEE. Never use BUYER, SELLER, "
    "TRUSTEE, LENDER, PURCHASER, or any other term.\n"
    "- Use GRANTOR for the party transferring, selling, or conveying rights.\n"
    "- Use GRANTEE for the party receiving, buying, or acquiring rights.\n"
    "- If the role is unclear, set party_type to null.\n"
    "- For individuals: split the full name into givenname and surname when possible.\n"
    "- designated_status captures roles like TRUSTEE or EXECUTOR that appear alongside the name "
    "(e.g. 'John Smith, Trustee'). Set to null if none is present.\n\n"
    "Example of correctly formatted parties:\n"
    '"individual_parties": [\n'
    '  {"name": "CURTIS M BAREFOOT", "party_type": "GRANTOR", "givenname": "CURTIS M", "surname": "BAREFOOT", "designated_status": null}\n'
    "]\n"
    '"firm_parties": [\n'
    '  {"name": "FIRST FEDERAL BANK", "party_type": "GRANTEE", "designated_status": null}\n'
    "]"
)


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.lstrip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.rstrip("`").strip()
    return stripped
