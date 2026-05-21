from __future__ import annotations

from django.utils import timezone
from temporalio import activity

from courtney.models import Book
from ..ctx import BookContext


@activity.defn
async def mark_book_processing_activity(book_ctx: BookContext, total_records: int) -> None:
    book = await Book.objects.filter(pk=book_ctx.pk).afirst()
    if not book:
        raise ValueError(f"Book {book_ctx.pk} not found")

    update = {
        "status": "processing",
        "total_records": total_records,
        "error_message": "",
    }
    if book.started_at is None:
        update["started_at"] = timezone.now()

    await Book.objects.filter(pk=book_ctx.pk).aupdate(**update)
