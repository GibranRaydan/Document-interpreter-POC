from __future__ import annotations

import re
import logging
from dataclasses import dataclass

from courtney.agents.landrecord.schemas.extraction import LandRecordExtraction

logger = logging.getLogger(__name__)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class ValidationResult:
    extraction: LandRecordExtraction
    is_valid: bool
    errors: list[str]
    confidence: float


def validate(extraction: LandRecordExtraction) -> ValidationResult:
    """
    Pure sync, rule-based validation of a LandRecordExtraction.
    Does not call any external service.
    """
    errors: list[str] = []

    if extraction.execution_date and not DATE_PATTERN.match(extraction.execution_date):
        errors.append(
            f"execution_date '{extraction.execution_date}' must be in YYYY-MM-DD format."
        )

    if extraction.consideration_amount is not None and extraction.consideration_amount < 0:
        errors.append("consideration_amount must be zero or positive.")

    for i, party in enumerate(extraction.parties):
        if not party.name and not party.givenname:
            errors.append(f"Party[{i}] must have at least a name or givenname.")
        if party.role and party.role not in ("GRANTOR", "GRANTEE"):
            errors.append(f"Party[{i}] role '{party.role}' is invalid (must be GRANTOR or GRANTEE).")

    return ValidationResult(
        extraction=extraction,
        is_valid=len(errors) == 0,
        errors=errors,
        confidence=_compute_confidence(extraction, errors),
    )


def _compute_confidence(extraction: LandRecordExtraction, errors: list[str]) -> float:
    score = 1.0
    key_fields = [
        extraction.book,
        extraction.page,
        extraction.document_type,
        extraction.property_address,
        extraction.execution_date,
        extraction.consideration_amount,
    ]
    score -= sum(1 for f in key_fields if f is None) * 0.1
    score -= len(errors) * 0.15
    return max(0.0, round(score, 2))
