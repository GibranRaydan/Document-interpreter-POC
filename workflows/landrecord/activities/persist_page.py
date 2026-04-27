from __future__ import annotations

from temporalio import activity

from courtney.models import Page
from ..ctx import PageOCRContext


@activity.defn
async def persist_page_activity(page_ocr_ctx: PageOCRContext) -> None:
    await Page.objects.filter(pk=page_ocr_ctx.page_pk).aupdate(raw_text=page_ocr_ctx.raw_text)
