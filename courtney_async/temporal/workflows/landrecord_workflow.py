from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from courtney_async.temporal.dto import (
        ProcessContext, OCRResultDTO, ClassifyResultDTO, ExtractResultDTO,
        ValidateResultDTO, PersistResultDTO, PipelineResult,
    )
    from courtney_async.temporal.activities.bootstrap import create_document_process_activity
    from courtney_async.temporal.activities.ocr import ocr_activity
    from courtney_async.temporal.activities.classify import classify_activity
    from courtney_async.temporal.activities.extract import extract_activity
    from courtney_async.temporal.activities.validate import validate_activity
    from courtney_async.temporal.activities.persist import persist_activity
    from courtney_async.temporal.config import DEFAULT_RETRY_POLICY


@workflow.defn
class LandRecordWorkflow:
    @workflow.run
    async def run(self, document_pk: int) -> PipelineResult:
        ctx: ProcessContext = await workflow.execute_activity(
            create_document_process_activity,
            document_pk,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        ocr: OCRResultDTO = await workflow.execute_activity(
            ocr_activity,
            ctx,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        # cls: ClassifyResultDTO = await workflow.execute_activity(
        #     classify_activity,
        #     args=[ctx, ocr.raw_text],
        #     start_to_close_timeout=timedelta(seconds=60),
        #     heartbeat_timeout=timedelta(seconds=20),
        #     retry_policy=DEFAULT_RETRY_POLICY,
        # )

        extr: ExtractResultDTO = await workflow.execute_activity(
            extract_activity,
            args=[ctx, ocr.raw_text],
            start_to_close_timeout=timedelta(seconds=180),
            # heartbeat_timeout=timedelta(seconds=20),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        val: ValidateResultDTO = await workflow.execute_activity(
            validate_activity,
            args=[ctx, extr.extraction],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )

        per: PersistResultDTO = await workflow.execute_activity(
            persist_activity,
            args=[ctx, val.normalized_extraction],
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        return PipelineResult(
            process_pk=ctx.process_pk,
            document_type="landrecord",
            is_valid=val.is_valid,
            confidence=val.confidence,
            errors=val.errors,
        )
