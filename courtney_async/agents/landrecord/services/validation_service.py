from __future__ import annotations

import re
import logging
from dataclasses import dataclass

from courtney_async.agents.landrecord.schemas.extraction import LandRecordExtraction

logger = logging.getLogger(__name__)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

VALID_ROLES = {"GRANTOR", "GRANTEE"}


@dataclass
class ValidationResult:
    extraction: LandRecordExtraction
    is_valid: bool
    errors: list[str]
    corrections: list[str]
    confidence: float


def _normalize_parties(extraction: LandRecordExtraction) -> tuple[LandRecordExtraction, list[str]]:
    corrections: list[str] = []

    normalized_individuals = []
    for i, party in enumerate(extraction.individual_parties):
        pt = party.party_type.strip().upper() if party.party_type else None
        if pt is not None and pt not in VALID_ROLES:
            corrections.append(f"individual_parties[{i}] party_type unrecognized: '{party.party_type}' → null")
            pt = None
        normalized_individuals.append(party.model_copy(update={"party_type": pt}))

    normalized_firms = []
    for i, party in enumerate(extraction.firm_parties):
        pt = party.party_type.strip().upper() if party.party_type else None
        if pt is not None and pt not in VALID_ROLES:
            corrections.append(f"firm_parties[{i}] party_type unrecognized: '{party.party_type}' → null")
            pt = None
        normalized_firms.append(party.model_copy(update={"party_type": pt}))

    return extraction.model_copy(update={
        "individual_parties": normalized_individuals,
        "firm_parties": normalized_firms,
    }), corrections


def validate(extraction: LandRecordExtraction) -> ValidationResult:
    normalized, corrections = _normalize_parties(extraction)
    errors: list[str] = []

    for date_field in ("execution_date", "recorded_date"):
        value = getattr(normalized, date_field)
        if value and not DATE_PATTERN.match(value):
            errors.append(f"{date_field} '{value}' must be in YYYY-MM-DD format.")

    if normalized.consideration_amount is not None and normalized.consideration_amount.strip() == "":
        errors.append("consideration_amount must not be empty.")

    for i, party in enumerate(normalized.individual_parties):
        if not party.name and not party.givenname and not party.surname:
            errors.append(f"individual_parties[{i}] must have at least one of: name, givenname, surname.")

    for i, party in enumerate(normalized.firm_parties):
        if not party.name:
            errors.append(f"firm_parties[{i}] must have a name.")

    if corrections:
        logger.info("Extraction normalized — %s", "; ".join(corrections))

    return ValidationResult(
        extraction=normalized,
        is_valid=len(errors) == 0,
        errors=errors,
        corrections=corrections,
        confidence=_compute_confidence(normalized, errors),
    )


def _compute_confidence(extraction: LandRecordExtraction, errors: list[str]) -> float:
    score = 1.0
    key_fields = [
        extraction.book, extraction.page, extraction.document_type,
        extraction.property_address, extraction.execution_date, extraction.consideration_amount,
    ]
    score -= sum(1 for f in key_fields if f is None) * 0.1
    score -= len(errors) * 0.15
    return max(0.0, round(score, 2))
