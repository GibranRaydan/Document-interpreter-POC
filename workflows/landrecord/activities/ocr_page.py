from __future__ import annotations

import httpx

from temporalio import activity

from core.langfuse import start_span_in_trace
from core.temporal import create_heartbeat_task

from ..ctx import PageContext, TraceContext, PageOCRContext
from ..ocr_helpers import WITH_TESSERACT, extract_with_llm, extract_with_tesseract


@activity.defn
async def ocr_page_activity(page_ctx: PageContext, trace_ctx: TraceContext) -> PageOCRContext:
    heartbeat_task = create_heartbeat_task(interval=10)
    try:
        async with httpx.AsyncClient() as client:
            with start_span_in_trace(trace_ctx.id, name=f"ocr.page.{page_ctx.pk}"):
                if WITH_TESSERACT:
                    raw_text = await extract_with_tesseract(page_ctx.file_path, client)
                else:
                    raw_text = await extract_with_llm(page_ctx.file_path, client)
    except Exception:
        raise
    finally:
        heartbeat_task.cancel()

    return PageOCRContext(page_pk=page_ctx.pk, raw_text=raw_text)
