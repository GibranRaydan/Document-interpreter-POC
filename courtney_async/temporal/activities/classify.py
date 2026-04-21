from __future__ import annotations

import logging

import httpx
from temporalio import activity

from courtney_async.temporal.dto import ProcessContext, ClassifyResultDTO
from ._shared import _load_agent, _set_step, _log

logger = logging.getLogger(__name__)

STEP = "classify"


@activity.defn
async def classify_activity(ctx: ProcessContext, raw_text: str) -> ClassifyResultDTO:
    from courtney_async.agents.landrecord.services.classifier_service import classify_document
    from courtney_async.agents.abstract.langfuse_client import start_span_in_trace

    await _set_step(ctx.process_pk, STEP)
    agent = await _load_agent("classifier")
    await _log(ctx.process_pk, STEP, "started")
    activity.heartbeat()

    try:
        async with httpx.AsyncClient() as client:
            try:
                with start_span_in_trace(ctx.trace_id, name="classify"):
                    result = await classify_document(raw_text, client, agent)
            except Exception:
                logger.debug("Langfuse span failed", exc_info=True)
                result = await classify_document(raw_text, client, agent)
    except Exception as exc:
        await _set_step(ctx.process_pk, f"{STEP}_failed")
        await _log(ctx.process_pk, STEP, "failed", detail=str(exc))
        raise

    await _set_step(ctx.process_pk, f"{STEP}_complete")
    await _log(ctx.process_pk, STEP, "completed", tokens_input=result.tokens_input, tokens_output=result.tokens_output)

    return ClassifyResultDTO(document_type=result.document_type, tokens_input=result.tokens_input, tokens_output=result.tokens_output)
