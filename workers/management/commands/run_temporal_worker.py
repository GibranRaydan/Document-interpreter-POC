import asyncio
import logging

from django.core.management.base import BaseCommand

from core.temporal import (
    temporal_address,
    temporal_task_queue,
    temporal_ocr_task_queue,
    temporal_book_task_queue,
    ocr_max_concurrent,
    book_max_concurrent_activities,
    book_max_concurrent_records,
)
from workers.worker import build_workers


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs three Temporal workers: orchestration, OCR, and Book."

    def handle(self, *args, **options):
        asyncio.run(self._run())

    async def _run(self):
        orchestration, ocr, book = await build_workers()

        self.stdout.write(self.style.SUCCESS(
            f"Orchestration worker started on {temporal_address()} task_queue={temporal_task_queue()}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"OCR worker started on {temporal_address()} task_queue={temporal_ocr_task_queue()} cap={ocr_max_concurrent()}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Book worker started on {temporal_address()} task_queue={temporal_book_task_queue()} "
            f"cap={book_max_concurrent_activities()} concurrent_records={book_max_concurrent_records()}"
        ))

        await asyncio.gather(orchestration.run(), ocr.run(), book.run())
