from __future__ import annotations

import logging
from temporalio import activity

from courtney_async.temporal.dto import ProcessContext, ExtractResultDTO, ValidateResultDTO
from ._shared import _set_step, _log

logger = logging.getLogger(__name__)

STEP = "validate"


@activity.defn
async def validate_activity(ctx: ProcessContext, extraction: dict) -> ValidateResultDTO:
    from courtney_async.agents.landrecord.services.validation_service import validate
    from courtney_async.agents.landrecord.schemas.extraction import LandRecordExtraction

    await _set_step(ctx.process_pk, STEP)
    await _log(ctx.process_pk, STEP, "started")

    try:
        parsed = LandRecordExtraction.model_validate(extraction)
        result = validate(parsed)
    except Exception as exc:
        await _set_step(ctx.process_pk, f"{STEP}_failed")
        await _log(ctx.process_pk, STEP, "failed", detail=str(exc))
        raise

    await _set_step(ctx.process_pk, f"{STEP}_complete")
    await _log(ctx.process_pk, STEP, "completed")

    return ValidateResultDTO(
        is_valid=result.is_valid,
        errors=result.errors,
        corrections=result.corrections,
        confidence=result.confidence,
        normalized_extraction=result.extraction.model_dump(),
    )
