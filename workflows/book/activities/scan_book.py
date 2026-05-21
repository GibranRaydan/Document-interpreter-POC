from __future__ import annotations

import logging
import os
from pathlib import Path

from asgiref.sync import sync_to_async
from temporalio import activity

from core.temporal import create_heartbeat_task
from courtney.models import Book
from ..ctx import BookContext, SubfolderContext


logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {".pdf", ".tiff", ".tif", ".png", ".jpg", ".jpeg"}


def _parse_book_start_page(name: str) -> int | None:
    try:
        return int(name)
    except ValueError:
        return None


def _has_supported_files(folder: Path) -> bool:
    for entry in folder.iterdir():
        if entry.is_file() and entry.suffix.lower() in ALLOWED_EXTENSIONS:
            return True
    return False


def _scan(folder_path: str) -> list[SubfolderContext]:
    root = Path(folder_path)
    if not root.is_dir():
        raise ValueError(f"folder_path is not a directory: {folder_path}")

    subfolders: list[SubfolderContext] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        if not _has_supported_files(entry):
            logger.warning("Skipping subfolder without supported files: %s", entry)
            continue
        subfolders.append(SubfolderContext(
            name=entry.name,
            path=str(entry),
            book_start_page=_parse_book_start_page(entry.name),
        ))
    return subfolders


@activity.defn
async def scan_book_activity(book_ctx: BookContext) -> list[SubfolderContext]:
    heartbeat = create_heartbeat_task(10)
    try:
        await Book.objects.filter(pk=book_ctx.pk).aupdate(
            status="scanning",
            name=os.path.basename(book_ctx.folder_path.rstrip(os.sep)),
            folder_path=book_ctx.folder_path,
        )
        subfolders = await sync_to_async(_scan, thread_sensitive=False)(book_ctx.folder_path)
        logger.info("Book %s: found %d subfolders", book_ctx.uuid, len(subfolders))
        return subfolders
    finally:
        heartbeat.cancel()
