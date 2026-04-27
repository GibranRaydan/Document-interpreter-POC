from __future__ import annotations

import logging

from temporalio import activity

from core.langfuse import get_langfuse
from courtney.models import Record
from ..ctx import RecordContext, TraceContext, ExtractContext


logger = logging.getLogger(__name__)


@activity.defn
async def persist_record_activity(
    record_ctx: RecordContext,
    trace_ctx: TraceContext,
    extract_ctx: ExtractContext,
) -> None:
    await Record.objects.filter(pk=record_ctx.pk).aupdate(
        data=extract_ctx.extraction,
        trace_id=trace_ctx.id,
    )
    try:
        get_langfuse().flush()
    except Exception:
        logger.error("Langfuse flush failed", exc_info=True)
