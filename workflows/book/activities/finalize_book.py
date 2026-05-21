from __future__ import annotations

from django.db.models import Count, Q
from django.utils import timezone
from temporalio import activity

from courtney.models import Book, Record
from ..ctx import BookContext


@activity.defn
async def finalize_book_activity(book_ctx: BookContext) -> None:
    aggregate = await Record.objects.filter(book_id=book_ctx.pk).aaggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status="completed")),
        failed=Count("id", filter=Q(status="failed")),
    )
    total = aggregate["total"] or 0
    completed = aggregate["completed"] or 0
    failed = aggregate["failed"] or 0

    if failed == 0 and completed == total and total > 0:
        status = "completed"
    elif failed > 0 and (completed + failed) >= total:
        status = "failed"
    else:
        status = "failed"

    await Book.objects.filter(pk=book_ctx.pk).aupdate(
        status=status,
        total_records=total,
        processed_records=completed,
        failed_records=failed,
        finished_at=timezone.now(),
    )
