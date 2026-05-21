from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy, WorkflowIDReusePolicy

with workflow.unsafe.imports_passed_through():
    from core.temporal import (
        DEFAULT_RETRY_POLICY,
        temporal_book_task_queue,
        temporal_task_queue,
        book_max_concurrent_records,
    )
    from workflows.landrecord.ctx import RecordContext
    from workflows.landrecord.workflow import LandRecordWorkflow
    from .ctx import BookContext, SubfolderContext
    from .activities.scan_book import scan_book_activity
    from .activities.mark_book_processing import mark_book_processing_activity
    from .activities.create_or_resume_record import create_or_resume_record_activity
    from .activities.mark_record_failed import mark_record_failed_activity
    from .activities.finalize_book import finalize_book_activity


@workflow.defn
class BookWorkflow:
    @workflow.run
    async def run(self, book_ctx: BookContext) -> None:
        BOOK_QUEUE = temporal_book_task_queue()
        ORCH_QUEUE = temporal_task_queue()

        subfolders: list[SubfolderContext] = await workflow.execute_activity(
            scan_book_activity,
            book_ctx,
            task_queue=BOOK_QUEUE,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        await workflow.execute_activity(
            mark_book_processing_activity,
            args=[book_ctx, len(subfolders)],
            task_queue=BOOK_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        sem = asyncio.Semaphore(book_max_concurrent_records())

        async def process_one(folder: SubfolderContext) -> None:
            async with sem:
                rec_ctx: RecordContext | None = await workflow.execute_activity(
                    create_or_resume_record_activity,
                    args=[book_ctx, folder],
                    task_queue=BOOK_QUEUE,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=DEFAULT_RETRY_POLICY,
                )
                if rec_ctx is None:
                    return

                try:
                    await workflow.execute_child_workflow(
                        LandRecordWorkflow.run,
                        rec_ctx,
                        id=f"landrecord-{rec_ctx.uuid}",
                        task_queue=ORCH_QUEUE,
                        id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE,
                    )
                except Exception as exc:
                    await workflow.execute_activity(
                        mark_record_failed_activity,
                        args=[rec_ctx, str(exc)],
                        task_queue=BOOK_QUEUE,
                        start_to_close_timeout=timedelta(seconds=15),
                        retry_policy=RetryPolicy(maximum_attempts=2),
                    )

        await asyncio.gather(*[process_one(folder) for folder in subfolders])

        await workflow.execute_activity(
            finalize_book_activity,
            book_ctx,
            task_queue=BOOK_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
