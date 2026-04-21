from __future__ import annotations

import logging
from datetime import datetime, timezone

import django
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _load_agent(name: str):
    from courtney_async.models import Agent
    return await Agent.objects.aget(name=name)


async def _set_step(process_pk: int, step: str) -> None:
    from courtney_async.models import DocumentProcess
    await DocumentProcess.objects.filter(pk=process_pk).aupdate(step=step)


async def _log(process_pk: int, step: str, status: str, agent=None, detail: str = "", **kwargs) -> None:
    from courtney_async.models import ProcessLog
    await ProcessLog.objects.acreate(
        process_id=process_pk,
        step=step,
        status=status,
        agent=agent,
        detail=detail,
        **kwargs,
    )
