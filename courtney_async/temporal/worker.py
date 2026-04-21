from __future__ import annotations

from django.conf import settings
from temporalio.client import Client
from temporalio.worker import Worker

from .workflows.landrecord_workflow import LandRecordWorkflow
from .activities import ALL_ACTIVITIES
from .config import temporal_address, temporal_namespace, temporal_task_queue


async def build_worker() -> Worker:
    client = await Client.connect(temporal_address(), namespace=temporal_namespace())
    return Worker(
        client,
        task_queue=temporal_task_queue(),
        workflows=[LandRecordWorkflow],
        activities=ALL_ACTIVITIES,
    )
