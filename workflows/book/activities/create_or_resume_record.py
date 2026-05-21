from __future__ import annotations

import logging
import re
from pathlib import Path

from asgiref.sync import sync_to_async
from django.db import transaction
from temporalio import activity

from courtney.models import Page, Record
from workflows.landrecord.ctx import RecordContext
from ..ctx import BookContext, SubfolderContext


logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {".pdf", ".tiff", ".tif", ".png", ".jpg", ".jpeg"}


def _parse_page_number(filename: str) -> int | None:
    stem = Path(filename).stem
    match = re.search(r"\d+", stem)
    if not match:
        return None
    try:
        return int(match.group())
    except ValueError:
        return None


def _list_page_files(folder: str) -> list[Path]:
    files: list[Path] = []
    for entry in sorted(Path(folder).iterdir(), key=lambda p: p.name):
        if entry.is_file() and entry.suffix.lower() in ALLOWED_EXTENSIONS:
            files.append(entry)
    return files


def _create_or_resume(book_pk: int, folder: SubfolderContext) -> RecordContext | None:
    with transaction.atomic():
        record = (
            Record.objects
            .select_for_update()
            .filter(book_id=book_pk, book_start_page=folder.book_start_page)
            .first()
        )

        if record and record.status == "completed":
            logger.info("Record %s already completed, skipping", record.uuid)
            return None

        if record is None:
            record = Record.objects.create(
                book_id=book_pk,
                book_start_page=folder.book_start_page,
                status="processing",
            )
            page_files = _list_page_files(folder.path)
            Page.objects.bulk_create([
                Page(
                    record=record,
                    file_path=str(f),
                    page_number=_parse_page_number(f.name),
                )
                for f in page_files
            ])
            logger.info("Record %s created with %d pages", record.uuid, len(page_files))
        else:
            record.status = "processing"
            record.error_message = ""
            record.save(update_fields=["status", "error_message", "updated"])
            logger.info("Record %s resumed from status=%s", record.uuid, record.status)

        return RecordContext(pk=record.pk, uuid=str(record.uuid))


@activity.defn
async def create_or_resume_record_activity(
    book_ctx: BookContext,
    folder: SubfolderContext,
) -> RecordContext | None:
    return await sync_to_async(_create_or_resume, thread_sensitive=False)(book_ctx.pk, folder)
