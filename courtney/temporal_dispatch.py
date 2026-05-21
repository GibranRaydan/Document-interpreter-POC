from __future__ import annotations

from asgiref.sync import async_to_sync
from temporalio.common import WorkflowIDReusePolicy

from core.temporal import get_temporal, temporal_task_queue, temporal_book_task_queue
from workflows.book.ctx import BookContext
from workflows.book.workflow import BookWorkflow
from workflows.landrecord.ctx import RecordContext
from workflows.landrecord.workflow import LandRecordWorkflow


async def _start_landrecord_workflow(record_pk: int, record_uuid: str) -> None:
    client = await get_temporal()
    await client.start_workflow(
        LandRecordWorkflow.run,
        RecordContext(pk=record_pk, uuid=record_uuid),
        id=f"landrecord-{record_uuid}",
        task_queue=temporal_task_queue(),
    )


async def _start_book_workflow(book_pk: int, book_uuid: str, folder_path: str) -> None:
    client = await get_temporal()
    await client.start_workflow(
        BookWorkflow.run,
        BookContext(pk=book_pk, uuid=book_uuid, folder_path=folder_path),
        id=f"book-{book_uuid}",
        task_queue=temporal_book_task_queue(),
        id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE,
    )


start_landrecord_workflow = async_to_sync(_start_landrecord_workflow)
start_book_workflow = async_to_sync(_start_book_workflow)
