from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TraceContext:
    id: str


@dataclass
class RecordContext:
    pk: int
    uuid: str


@dataclass
class PageContext:
    pk: int
    record_pk: int
    file_path: str


@dataclass
class PageOCRContext:
    page_pk: int
    raw_text: str


@dataclass
class ExtractContext:
    record_pk: int
    extraction: dict
