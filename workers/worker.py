from __future__ import annotations

from temporalio.client import Client
from temporalio.worker import Worker

from core.temporal import (
    temporal_address,
    temporal_namespace,
    temporal_task_queue,
    temporal_ocr_task_queue,
    temporal_book_task_queue,
    ocr_max_concurrent,
    book_max_concurrent_activities,
)

from workflows.landrecord.workflow import LandRecordWorkflow, PageWorkflow
from workflows.landrecord.activities import (
    bootstrap_activity,
    list_pages_activity,
    ocr_page_activity,
    persist_page_activity,
    extract_activity,
    persist_record_activity,
)
from workflows.book.workflow import BookWorkflow
from workflows.book.activities import (
    scan_book_activity,
    mark_book_processing_activity,
    create_or_resume_record_activity,
    mark_record_failed_activity,
    finalize_book_activity,
)


async def build_workers() -> tuple[Worker, Worker, Worker]:
    client = await Client.connect(temporal_address(), namespace=temporal_namespace())

    orchestration = Worker(
        client,
        task_queue=temporal_task_queue(),
        workflows=[LandRecordWorkflow, PageWorkflow],
        activities=[
            bootstrap_activity,
            list_pages_activity,
            extract_activity,
            persist_record_activity,
        ],
    )

    ocr = Worker(
        client,
        task_queue=temporal_ocr_task_queue(),
        workflows=[],
        activities=[
            ocr_page_activity,
            persist_page_activity,
        ],
        max_concurrent_activities=ocr_max_concurrent(),
    )

    book = Worker(
        client,
        task_queue=temporal_book_task_queue(),
        workflows=[BookWorkflow],
        activities=[
            scan_book_activity,
            mark_book_processing_activity,
            create_or_resume_record_activity,
            mark_record_failed_activity,
            finalize_book_activity,
        ],
        max_concurrent_activities=book_max_concurrent_activities(),
    )

    return orchestration, ocr, book
