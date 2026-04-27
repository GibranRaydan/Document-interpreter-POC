from __future__ import annotations

from asgiref.sync import async_to_sync

from core.temporal import get_temporal, temporal_task_queue
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

start_landrecord_workflow = async_to_sync(_start_landrecord_workflow)
