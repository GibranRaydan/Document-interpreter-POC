import asyncio
import logging

from django.core.management.base import BaseCommand

from courtney_async.temporal.config import temporal_task_queue, temporal_address
from courtney_async.temporal.worker import build_worker

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs a Temporal worker polling the configured task queue."

    def handle(self, *args, **options):
        asyncio.run(self._run())

    async def _run(self):
        worker = await build_worker()
        self.stdout.write(
            self.style.SUCCESS(
                f"Temporal worker started on {temporal_address()} task_queue={temporal_task_queue()}"
            )
        )
        await worker.run()
