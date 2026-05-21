from __future__ import annotations

from temporalio import activity

from courtney.models import Page
from ..ctx import RecordContext, PageContext


@activity.defn
async def list_pages_activity(record_ctx: RecordContext) -> list[PageContext]:
    pages = []
    async for page in Page.objects.filter(record_id=record_ctx.pk).order_by("page_number", "id"):
        file_path = page.file_path or (page.file.path if page.file else "")
        if not file_path:
            raise ValueError(f"Page {page.pk} has neither file nor file_path")
        pages.append(PageContext(pk=page.pk, record_pk=record_ctx.pk, file_path=file_path))
    return pages
