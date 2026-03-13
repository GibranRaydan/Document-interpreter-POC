import re
import logging
from typing import Any

from agents.schemas.document_schemas import SCHEMAS_MAP

logger = logging.getLogger(__name__)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(data: dict, doc_type: str) -> dict:
    """
    Pure sync validation. Does not call any external service.

    Adds a '_validation' key to a copy of `data` containing:
      - confidence: float 0.0-1.0
      - errors: list of str
      - is_valid: bool

    Returns the modified dict (does NOT mutate the original).
    """
    errors: list[str] = []
    schema_class = SCHEMAS_MAP.get(doc_type)

    # --- Schema-level validation using Pydantic ---
    if schema_class:
        try:
            schema_class.model_validate(data)
        except Exception as exc:
            # Pydantic ValidationError has .errors() but we catch broadly
            try:
                for err in exc.errors():  # type: ignore[attr-defined]
                    field = ".".join(str(loc) for loc in err["loc"])
                    errors.append(f"Field '{field}': {err['msg']}")
            except AttributeError:
                errors.append(str(exc))

    # --- Date format validation ---
    date_fields = _find_date_fields(data)
    for field_path, value in date_fields:
        if value and not DATE_PATTERN.match(str(value)):
            errors.append(
                f"Date field '{field_path}' has unexpected format: '{value}' "
                f"(expected YYYY-MM-DD)"
            )

    # --- Invoice-specific: total vs line_items sum ---
    if doc_type == "invoice":
        errors.extend(_validate_invoice_totals(data))

    # --- Compute confidence ---
    confidence = _compute_confidence(data, schema_class, errors)

    result = dict(data)
    result["_validation"] = {
        "confidence": confidence,
        "errors": errors,
        "is_valid": len(errors) == 0,
    }
    return result


def _find_date_fields(data: dict, prefix: str = "") -> list[tuple[str, Any]]:
    """Recursively find keys named 'date' or ending in '_date'."""
    found = []
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if key == "date" or key.endswith("_date"):
            found.append((path, value))
        elif isinstance(value, dict):
            found.extend(_find_date_fields(value, path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    found.extend(_find_date_fields(item, f"{path}[{i}]"))
    return found


def _validate_invoice_totals(data: dict) -> list[str]:
    """
    For invoices: verify that total_amount ≈ subtotal + tax.
    Also verify that total_amount ≈ sum(line_items[*].total).
    Allows 1% tolerance to handle rounding.
    """
    errors = []
    total_amount = data.get("total_amount")
    subtotal = data.get("subtotal")
    tax = data.get("tax")
    line_items = data.get("line_items", [])

    if total_amount is None:
        return errors

    try:
        total_amount_f = float(total_amount)
    except (TypeError, ValueError):
        return errors

    tolerance = total_amount_f * 0.01

    # Check subtotal + tax
    if subtotal is not None and tax is not None:
        try:
            subtotal_f = float(subtotal)
            tax_f = float(tax)
            computed_total = subtotal_f + tax_f
            if abs(total_amount_f - computed_total) > tolerance:
                errors.append(
                    f"Invoice total_amount ({total_amount_f:.2f}) does not match "
                    f"subtotal + tax ({computed_total:.2f})"
                )
        except (TypeError, ValueError):
            pass

    # Check line_items sum
    if line_items:
        try:
            items_sum = sum(
                float(item.get("total", 0) or 0)
                for item in line_items
                if isinstance(item, dict)
            )
            if items_sum > 0 and abs(total_amount_f - items_sum) > tolerance:
                errors.append(
                    f"Invoice total_amount ({total_amount_f:.2f}) does not match "
                    f"sum of line_items ({items_sum:.2f})"
                )
        except (TypeError, ValueError):
            pass

    return errors


def _compute_confidence(
    data: dict,
    schema_class: type | None,
    errors: list[str],
) -> float:
    """
    Confidence heuristic:
    - Starts at 1.0
    - Deducts 0.2 per validation error (minimum 0.0)
    - If no schema is found, deducts 0.3 (unknown document type)
    - If data is empty, returns 0.0
    """
    if not data:
        return 0.0

    score = 1.0
    if schema_class is None:
        score -= 0.3
    score -= len(errors) * 0.2
    return max(0.0, round(score, 2))
