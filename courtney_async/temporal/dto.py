from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProcessContext:
    document_pk: int
    process_pk: int
    document_file_path: str
    trace_id: str


@dataclass
class OCRResultDTO:
    raw_text: str
    tokens_input: int
    tokens_output: int


@dataclass
class ClassifyResultDTO:
    document_type: str
    tokens_input: int
    tokens_output: int


@dataclass
class ExtractResultDTO:
    extraction: dict  # serialized LandRecordExtraction.model_dump()
    tokens_input: int
    tokens_output: int


@dataclass
class ValidateResultDTO:
    is_valid: bool
    errors: list[str]
    corrections: list[str]
    confidence: float
    normalized_extraction: dict


@dataclass
class PersistResultDTO:
    process_pk: int
    step: str


@dataclass
class PipelineResult:
    process_pk: int
    document_type: str
    is_valid: bool
    confidence: float
    errors: list[str] = field(default_factory=list)
