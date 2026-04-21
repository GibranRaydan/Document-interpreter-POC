from __future__ import annotations

import uuid
import logging
from datetime import timedelta

from django.conf import settings
from temporalio import activity

from courtney_async.temporal.dto import ProcessContext
from ._shared import _set_step, _log, _now_iso

logger = logging.getLogger(__name__)

STEP = "bootstrap"


@activity.defn
async def create_document_process_activity(document_pk: int) -> ProcessContext:
    from courtney_async.models import Document, DocumentProcess
    from courtney_async.agents.abstract.langfuse_client import get_langfuse

    activity.heartbeat()

    document = await Document.objects.aget(pk=document_pk)

    version = await DocumentProcess.objects.filter(document=document).acount() + 1
    import uuid as _uuid
    from django.utils.text import slugify
    process = await DocumentProcess.objects.acreate(
        document=document,
        slug=slugify(str(_uuid.uuid4()))[:50],
        version=version,
        step=STEP,
    )

    trace_id = _uuid.uuid4().hex

    try:
        lf = get_langfuse()
        lf.trace(id=trace_id, name="land-record-pipeline", metadata={"document_pk": document_pk})
    except Exception:
        logger.debug("Langfuse trace creation failed", exc_info=True)

    await _log(process.pk, STEP, "completed", detail=f"trace_id={trace_id}")

    file_path = document.file.path

    return ProcessContext(
        document_pk=document_pk,
        process_pk=process.pk,
        document_file_path=file_path,
        trace_id=trace_id,
    )
