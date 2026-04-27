import asyncio
import logging

from django.core.management.base import BaseCommand

from core.temporal import (
    temporal_address,
    temporal_task_queue,
    temporal_ocr_task_queue,
    ocr_max_concurrent,
)
from workers.worker import build_workers


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs two Temporal workers: orchestration and OCR."

    def handle(self, *args, **options):
        asyncio.run(self._run())

    async def _run(self):
        orchestration, ocr = await build_workers()

        self.stdout.write(self.style.SUCCESS(
            f"Orchestration worker started on {temporal_address()} task_queue={temporal_task_queue()}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"OCR worker started on {temporal_address()} task_queue={temporal_ocr_task_queue()} cap={ocr_max_concurrent()}"
        ))

        await asyncio.gather(orchestration.run(), ocr.run())
