from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from core.temporal import DEFAULT_RETRY_POLICY, temporal_task_queue, temporal_ocr_task_queue
    from .ctx import RecordContext, TraceContext, PageContext, PageOCRContext, ExtractContext
    from .activities.bootstrap import bootstrap_activity
    from .activities.list_pages import list_pages_activity
    from .activities.ocr_page import ocr_page_activity
    from .activities.persist_page import persist_page_activity
    from .activities.extract import extract_activity
    from .activities.persist_record import persist_record_activity


@workflow.defn
class PageWorkflow:
    @workflow.run
    async def run(self, page_ctx: PageContext, trace_ctx: TraceContext) -> None:
        OCR_QUEUE = temporal_ocr_task_queue()

        page_ocr_ctx: PageOCRContext = await workflow.execute_activity(
            ocr_page_activity,
            args=[page_ctx, trace_ctx],
            task_queue=OCR_QUEUE,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        await workflow.execute_activity(
            persist_page_activity,
            page_ocr_ctx,
            task_queue=OCR_QUEUE,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=DEFAULT_RETRY_POLICY,
        )


@workflow.defn
class LandRecordWorkflow:
    @workflow.run
    async def run(self, record_ctx: RecordContext) -> None:
        ORCH_QUEUE = temporal_task_queue()

        trace_ctx: TraceContext = await workflow.execute_activity(
            bootstrap_activity,
            record_ctx,
            task_queue=ORCH_QUEUE,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        pages: list[PageContext] = await workflow.execute_activity(
            list_pages_activity,
            record_ctx,
            task_queue=ORCH_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        await asyncio.gather(*[
            workflow.execute_child_workflow(
                PageWorkflow.run,
                args=[page, trace_ctx],
                id=f"page-{page.pk}",
                task_queue=ORCH_QUEUE,
            )
            for page in pages
        ])

        extract_ctx: ExtractContext = await workflow.execute_activity(
            extract_activity,
            args=[record_ctx, trace_ctx],
            task_queue=ORCH_QUEUE,
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        await workflow.execute_activity(
            persist_record_activity,
            args=[record_ctx, trace_ctx, extract_ctx],
            task_queue=ORCH_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
