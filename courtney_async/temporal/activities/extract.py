from __future__ import annotations

import logging

import httpx
from temporalio import activity

from courtney_async.temporal.dto import ProcessContext, ExtractResultDTO
from ._shared import _load_agent, _set_step, _log

logger = logging.getLogger(__name__)

STEP = "extract"


@activity.defn
async def extract_activity(ctx: ProcessContext, raw_text: str) -> ExtractResultDTO:
    from courtney_async.agents.landrecord.services.extraction_service import extract_structured_data
    from courtney_async.agents.abstract.langfuse_client import start_span_in_trace

    await _set_step(ctx.process_pk, STEP)
    agent = await _load_agent("extractor")
    await _log(ctx.process_pk, STEP, "started")
    activity.heartbeat()

    try:
        async with httpx.AsyncClient() as client:
            try:
                with start_span_in_trace(ctx.trace_id, name="extract"):
                    result = await extract_structured_data(raw_text, client, agent)
            except Exception:
                logger.debug("Langfuse span failed", exc_info=True)
                result = await extract_structured_data(raw_text, client, agent)
    except Exception as exc:
        await _set_step(ctx.process_pk, f"{STEP}_failed")
        await _log(ctx.process_pk, STEP, "failed", detail=str(exc))
        raise

    await _set_step(ctx.process_pk, f"{STEP}_complete")
    await _log(ctx.process_pk, STEP, "completed", tokens_input=result.tokens_input, tokens_output=result.tokens_output)

    return ExtractResultDTO(
        extraction=result.extraction.model_dump(),
        tokens_input=result.tokens_input,
        tokens_output=result.tokens_output,
    )
