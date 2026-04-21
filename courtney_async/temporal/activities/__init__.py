from .bootstrap import create_document_process_activity
from .ocr import ocr_activity
from .classify import classify_activity
from .extract import extract_activity
from .validate import validate_activity
from .persist import persist_activity

ALL_ACTIVITIES = [
    create_document_process_activity,
    ocr_activity,
    classify_activity,
    extract_activity,
    validate_activity,
    persist_activity,
]
