from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import httpx
from temporalio import activity

from courtney_async.temporal.dto import ProcessContext, OCRResultDTO
from ._shared import _load_agent, _set_step, _log

logger = logging.getLogger(__name__)

STEP = "ocr"


@activity.defn
async def ocr_activity(ctx: ProcessContext) -> OCRResultDTO:
    from courtney_async.agents.landrecord.services.ocr_service import extract_text
    from courtney_async.agents.abstract.langfuse_client import start_span_in_trace

    await _set_step(ctx.process_pk, STEP)
    agent = await _load_agent("ocr")
    await _log(ctx.process_pk, STEP, "started")

    async def _heartbeat_loop():
        while True:
            await asyncio.sleep(10)
            activity.heartbeat()

    heartbeat_task = asyncio.create_task(_heartbeat_loop())

    try:
        async with httpx.AsyncClient() as client:
            try:
                with start_span_in_trace(ctx.trace_id, name="ocr"):
                    result = await extract_text(ctx.document_file_path, client, agent)
            except Exception:
                logger.debug("Langfuse span failed", exc_info=True)
                result = await extract_text(ctx.document_file_path, client, agent)
    except Exception as exc:
        await _set_step(ctx.process_pk, f"{STEP}_failed")
        await _log(ctx.process_pk, STEP, "failed", detail=str(exc))
        raise
    finally:
        heartbeat_task.cancel()

    await _set_step(ctx.process_pk, f"{STEP}_complete")
    await _log(ctx.process_pk, STEP, "completed", tokens_input=result.tokens_input, tokens_output=result.tokens_output)

    return OCRResultDTO(raw_text=result.raw_text, tokens_input=result.tokens_input, tokens_output=result.tokens_output)
