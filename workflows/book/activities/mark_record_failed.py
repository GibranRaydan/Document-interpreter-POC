from __future__ import annotations

from django.db.models import F
from temporalio import activity

from courtney.models import Book, Record
from workflows.landrecord.ctx import RecordContext


@activity.defn
async def mark_record_failed_activity(record_ctx: RecordContext, error: str) -> None:
    await Record.objects.filter(pk=record_ctx.pk).aupdate(
        status="failed",
        error_message=error[:4000],
    )
    record = await Record.objects.filter(pk=record_ctx.pk).only("book_id").afirst()
    if record and record.book_id:
        await Book.objects.filter(pk=record.book_id).aupdate(
            failed_records=F("failed_records") + 1,
        )
