import re
from decimal import Decimal, InvalidOperation

from django.db import transaction

from courtney_async.agents.landrecord.schemas.extraction import LandRecordExtraction
from courtney_async.models import DocumentProcess, LandRecord, Party, Reference


def _parse_date(value: str | None):
    if not value:
        return None
    from datetime import date
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_amount(value: str | None) -> Decimal | None:
    if not value:
        return None
    cleaned = re.sub(r"[^\d.]", "", value)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def select_process(process: DocumentProcess) -> LandRecord:
    with transaction.atomic():
        DocumentProcess.objects.filter(
            document=process.document, is_selected=True
        ).exclude(pk=process.pk).update(is_selected=False)

        process.is_selected = True
        process.save(update_fields=["is_selected"])

        extraction = LandRecordExtraction.model_validate(process.data or {})

        land_record, _ = LandRecord.objects.update_or_create(
            process=process,
            defaults={
                "book": extraction.book,
                "page": extraction.page,
                "document_type": extraction.document_type,
                "page_range": extraction.page_range,
                "property_address": extraction.property_address,
                "legal_description": extraction.legal_description,
                "consideration_amount": _parse_amount(extraction.consideration_amount),
                "execution_date": _parse_date(extraction.execution_date),
                "county": extraction.county,
                "state": extraction.state,
            },
        )

        Party.objects.filter(land_record=land_record).delete()
        Reference.objects.filter(land_record=land_record).delete()

        Party.objects.bulk_create([
            Party(land_record=land_record, name=p.name, givenname=p.givenname, role=p.role, type=p.type)
            for p in extraction.parties
        ])
        Reference.objects.bulk_create([
            Reference(land_record=land_record, book=r.book, page=r.page, document_type=r.document_type)
            for r in extraction.references
        ])

    return land_record
