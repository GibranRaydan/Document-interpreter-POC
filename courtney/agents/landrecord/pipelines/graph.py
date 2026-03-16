from __future__ import annotations

import json
import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

import httpx
from django.utils.text import slugify
from langgraph.graph import StateGraph, END

from courtney.models import Agent, Document, DocumentProcess, ProcessLog, StepStatus
from courtney.agents.landrecord.schemas.extraction import LandRecordExtraction
from courtney.agents.landrecord.services import (
    ocr_service,
    classifier_service,
    extraction_service,
    validation_service,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pipeline state
# ---------------------------------------------------------------------------

class LandRecordPipelineState(TypedDict):
    document_pk: int
    process_pk: int
    file_path: str
    raw_text: str
    document_type: str
    extraction: dict | None
    is_valid: bool
    errors: list[str]
    confidence: float
    failed_step: str
    error_message: str
    _client: Any                  # httpx.AsyncClient shared across nodes
    last_event: dict | None       # unified SSE event emitted after each node


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_agent(name: str) -> Agent:
    return await Agent.objects.aget(name=name)


async def _log(
    process_pk: int,
    step: str,
    status: str,
    agent: Agent | None,
    detail: str = "",
    duration_ms: int | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
) -> None:
    await ProcessLog.objects.acreate(
        process_id=process_pk,
        step=step,
        status=status,
        agent=agent,
        detail=detail,
        duration_ms=duration_ms,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
    )


async def _set_step(process_pk: int, step: str) -> None:
    await DocumentProcess.objects.filter(pk=process_pk).aupdate(step=step)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_date(date_str: str | None):
    if not date_str:
        return None
    from datetime import date
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None


def _event(
    step: str,
    status: str,
    model: str,
    started_at: str,
    duration_ms: int | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    output: Any = None,
) -> dict:
    return {
        "step": step,
        "status": status,
        "model": model,
        "started_at": started_at,
        "duration_ms": duration_ms,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "output": output,
    }


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def ocr_node(state: LandRecordPipelineState) -> LandRecordPipelineState:
    agent = await _load_agent("ocr")
    started_at = _now_iso()
    await _set_step(state["process_pk"], "ocr")
    await _log(state["process_pk"], "ocr", StepStatus.STARTED, agent)

    start = time.monotonic()
    try:
        result = await ocr_service.extract_text(state["file_path"], state["_client"], agent)
    except Exception as exc:
        logger.exception("OCR failed for process %d", state["process_pk"])
        await _log(state["process_pk"], "ocr", StepStatus.FAILED, agent, detail=str(exc))
        await _set_step(state["process_pk"], "ocr_failed")
        return {
            **state,
            "failed_step": "ocr",
            "error_message": str(exc),
            "last_event": _event("ocr", "failed", agent.model, started_at, output=str(exc)),
        }

    duration = int((time.monotonic() - start) * 1000)
    await _log(
        state["process_pk"], "ocr", StepStatus.COMPLETED, agent,
        detail=result.raw_text,
        duration_ms=duration,
        tokens_input=result.tokens_input,
        tokens_output=result.tokens_output,
    )
    await DocumentProcess.objects.filter(pk=state["process_pk"]).aupdate(
        raw_text=result.raw_text, step="ocr_complete"
    )
    return {
        **state,
        "raw_text": result.raw_text,
        "last_event": _event(
            "ocr", "completed", agent.model, started_at,
            duration_ms=duration,
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            output=result.raw_text,
        ),
    }


async def classify_node(state: LandRecordPipelineState) -> LandRecordPipelineState:
    agent = await _load_agent("classifier")
    started_at = _now_iso()
    await _set_step(state["process_pk"], "classify")
    await _log(state["process_pk"], "classify", StepStatus.STARTED, agent)

    start = time.monotonic()
    try:
        result = await classifier_service.classify_document(state["raw_text"], state["_client"], agent)
    except Exception as exc:
        logger.exception("Classification failed for process %d", state["process_pk"])
        await _log(state["process_pk"], "classify", StepStatus.FAILED, agent, detail=str(exc))
        await _set_step(state["process_pk"], "classify_failed")
        return {
            **state,
            "failed_step": "classify",
            "error_message": str(exc),
            "last_event": _event("classify", "failed", agent.model, started_at, output=str(exc)),
        }

    duration = int((time.monotonic() - start) * 1000)
    await _log(
        state["process_pk"], "classify", StepStatus.COMPLETED, agent,
        duration_ms=duration,
        tokens_input=result.tokens_input,
        tokens_output=result.tokens_output,
    )
    await DocumentProcess.objects.filter(pk=state["process_pk"]).aupdate(step="classify_complete")
    return {
        **state,
        "document_type": result.document_type,
        "last_event": _event(
            "classify", "completed", agent.model, started_at,
            duration_ms=duration,
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            output=result.document_type,
        ),
    }


async def extract_node(state: LandRecordPipelineState) -> LandRecordPipelineState:
    agent = await _load_agent("extractor")
    started_at = _now_iso()
    await _set_step(state["process_pk"], "extract")
    await _log(state["process_pk"], "extract", StepStatus.STARTED, agent)

    start = time.monotonic()
    try:
        result = await extraction_service.extract_structured_data(
            state["raw_text"], state["_client"], agent
        )
    except Exception as exc:
        logger.exception("Extraction failed for process %d", state["process_pk"])
        await _log(state["process_pk"], "extract", StepStatus.FAILED, agent, detail=str(exc))
        await _set_step(state["process_pk"], "extract_failed")
        return {
            **state,
            "failed_step": "extract",
            "error_message": str(exc),
            "last_event": _event("extract", "failed", agent.model, started_at, output=str(exc)),
        }

    duration = int((time.monotonic() - start) * 1000)
    extraction_dict = result.extraction.model_dump(mode="json")
    await _log(
        state["process_pk"], "extract", StepStatus.COMPLETED, agent,
        detail=result.extraction.model_dump_json(),
        duration_ms=duration,
        tokens_input=result.tokens_input,
        tokens_output=result.tokens_output,
    )
    await _set_step(state["process_pk"], "extract_complete")
    return {
        **state,
        "extraction": extraction_dict,
        "last_event": _event(
            "extract", "completed", agent.model, started_at,
            duration_ms=duration,
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            output=extraction_dict,
        ),
    }


async def validate_node(state: LandRecordPipelineState) -> LandRecordPipelineState:
    agent = await _load_agent("validator")
    started_at = _now_iso()
    await _set_step(state["process_pk"], "validate")
    await _log(state["process_pk"], "validate", StepStatus.STARTED, agent)

    start = time.monotonic()
    extraction = LandRecordExtraction.model_validate(state["extraction"] or {})
    result = validation_service.validate(extraction)
    duration = int((time.monotonic() - start) * 1000)

    await _log(
        state["process_pk"], "validate", StepStatus.COMPLETED, agent,
        detail="; ".join(result.errors) if result.errors else "ok",
        duration_ms=duration,
    )
    await _set_step(state["process_pk"], "validate_complete")
    output = {"is_valid": result.is_valid, "errors": result.errors, "confidence": result.confidence}
    return {
        **state,
        "is_valid": result.is_valid,
        "errors": result.errors,
        "confidence": result.confidence,
        "last_event": _event(
            "validate", "completed", agent.model, started_at,
            duration_ms=duration,
            output=output,
        ),
    }


async def persist_node(state: LandRecordPipelineState) -> LandRecordPipelineState:
    """Saves the extraction result as JSON into DocumentProcess.data."""
    started_at = _now_iso()
    extraction_data = state["extraction"] or {}
    await DocumentProcess.objects.filter(pk=state["process_pk"]).aupdate(
        data=extraction_data,
        step="complete",
    )
    return {
        **state,
        "last_event": _event(
            "persist", "completed", "", started_at,
            output={"process_pk": state["process_pk"], "step": "complete"},
        ),
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _should_continue(state: LandRecordPipelineState) -> str:
    return "end" if state["failed_step"] else "continue"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def _build_graph() -> Any:
    graph = StateGraph(LandRecordPipelineState)

    graph.add_node("ocr", ocr_node)
    graph.add_node("classify", classify_node)
    graph.add_node("extract", extract_node)
    graph.add_node("validate", validate_node)
    graph.add_node("persist", persist_node)

    graph.set_entry_point("ocr")
    graph.add_conditional_edges("ocr", _should_continue, {"continue": "classify", "end": END})
    graph.add_conditional_edges("classify", _should_continue, {"continue": "extract", "end": END})
    graph.add_conditional_edges("extract", _should_continue, {"continue": "validate", "end": END})
    graph.add_conditional_edges("validate", _should_continue, {"continue": "persist", "end": END})
    graph.add_edge("persist", END)

    return graph.compile()


pipeline = _build_graph()


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

async def _make_initial_state(document_pk: int, client: httpx.AsyncClient) -> LandRecordPipelineState:
    document = await Document.objects.aget(pk=document_pk)
    last_version = await DocumentProcess.objects.filter(document=document).acount()
    process = await DocumentProcess.objects.acreate(
        document=document,
        slug=slugify(str(uuid.uuid4()))[:50],
        version=last_version + 1,
        step="pending",
    )
    return {
        "document_pk": document_pk,
        "process_pk": process.pk,
        "file_path": document.file.path,
        "raw_text": "",
        "document_type": "",
        "extraction": None,
        "is_valid": False,
        "errors": [],
        "confidence": 0.0,
        "failed_step": "",
        "error_message": "",
        "_client": client,
        "last_event": None,
    }


async def run_pipeline(document_pk: int) -> LandRecordPipelineState:
    """
    Runs the full extraction pipeline and returns the final state.
    DocumentProcess.data will contain the JSON result.
    """
    async with httpx.AsyncClient() as client:
        initial_state = await _make_initial_state(document_pk, client)
        return await pipeline.ainvoke(initial_state)


async def run_pipeline_stream(document_pk: int):
    """
    Async generator that runs the pipeline and yields one SSE event dict
    per completed node. Used by the streaming endpoint.
    """
    async with httpx.AsyncClient() as client:
        initial_state = await _make_initial_state(document_pk, client)
        async for chunk in pipeline.astream(initial_state):
            for _node_name, state_diff in chunk.items():
                event = state_diff.get("last_event")
                if event:
                    yield event
