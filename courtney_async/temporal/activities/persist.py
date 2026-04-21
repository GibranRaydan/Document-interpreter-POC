from __future__ import annotations

import logging
from temporalio import activity

from courtney_async.temporal.dto import ProcessContext, PersistResultDTO
from ._shared import _set_step, _log

logger = logging.getLogger(__name__)

STEP = "persist"


@activity.defn
async def persist_activity(ctx: ProcessContext, extraction: dict) -> PersistResultDTO:
    from courtney_async.models import DocumentProcess
    from courtney_async.agents.abstract.langfuse_client import get_langfuse

    await _set_step(ctx.process_pk, STEP)
    await _log(ctx.process_pk, STEP, "started")

    try:
        await DocumentProcess.objects.filter(pk=ctx.process_pk).aupdate(
            data=extraction,
            raw_text="",  # raw_text already stored in OCR step via DB if needed
            step="complete",
        )
    except Exception as exc:
        await _set_step(ctx.process_pk, f"{STEP}_failed")
        await _log(ctx.process_pk, STEP, "failed", detail=str(exc))
        raise

    await _log(ctx.process_pk, STEP, "completed")

    try:
        get_langfuse().flush()
    except Exception:
        logger.debug("Langfuse flush failed", exc_info=True)

    return PersistResultDTO(process_pk=ctx.process_pk, step="complete")
