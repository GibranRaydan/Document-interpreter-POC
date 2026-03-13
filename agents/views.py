import json
import logging

import httpx
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .models import Document, Status
from .serializers import DocumentUploadSerializer, DocumentDetailSerializer
from .services import ocr_agent, classifier_agent, extraction_agent, validation_agent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: SSE event formatter
# ---------------------------------------------------------------------------

def sse_event(event: str, data: dict) -> str:
    """
    Formats a single SSE event frame.
    The trailing double newline is mandatory per the SSE specification.
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


# ---------------------------------------------------------------------------
# View 1: POST /api/agents/documents/
# ---------------------------------------------------------------------------

class DocumentUploadView(APIView):
    """
    Accepts a multipart/form-data POST with a 'file' field.
    Creates a Document record with status='pending'.
    Returns the document ID and the SSE stream URL.
    """

    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = serializer.save(status=Status.PENDING)

        return Response(
            {
                "id": document.pk,
                "stream_url": f"/api/agents/documents/{document.pk}/process/",
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# View 2: GET /api/agents/documents/<id>/process/
# ---------------------------------------------------------------------------

class DocumentProcessView(View):
    """
    Returns a Server-Sent Events stream that runs the full pipeline:
    ocr → classify → extract → validate

    Each stage emits SSE events so the client can display progress in real time.
    """

    async def get(self, request, pk: int):
        try:
            document = await Document.objects.aget(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({"error": "Document not found."}, status=404)

        if document.status == Status.COMPLETED:
            return JsonResponse({"error": "Document already processed."}, status=409)

        response = StreamingHttpResponse(
            self._run_pipeline(document),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # Disable nginx buffering if behind a proxy
        return response

    async def _run_pipeline(self, document: Document):
        """
        Async generator that runs the pipeline and yields SSE event strings.
        Django's StreamingHttpResponse consumes this generator and streams
        each yielded chunk to the client immediately.
        """
        # Update status to processing
        document.status = Status.PROCESSING
        await document.asave(update_fields=["status", "updated_at"])

        yield sse_event("progress", {"step": "ocr", "message": "Starting OCR..."})

        file_path = document.file.path  # Absolute filesystem path via FileFieldFile

        async with httpx.AsyncClient() as client:
            # --- Stage 1: OCR ---
            try:
                raw_text = await ocr_agent.extract_text(file_path, client)
            except Exception as exc:
                logger.exception("OCR failed for document %d", document.pk)
                document.status = Status.FAILED
                document.error_message = f"OCR failed: {exc}"
                await document.asave(
                    update_fields=["status", "error_message", "updated_at"]
                )
                yield sse_event("error", {"step": "ocr", "message": str(exc)})
                return

            document.raw_text = raw_text
            await document.asave(update_fields=["raw_text", "updated_at"])
            yield sse_event(
                "step_complete",
                {
                    "step": "ocr",
                    "message": "Text extracted successfully.",
                    "preview": raw_text[:200],
                },
            )

            # --- Stage 2: Classify ---
            yield sse_event(
                "progress",
                {"step": "classify", "message": "Classifying document..."},
            )
            try:
                doc_type = await classifier_agent.classify_document(raw_text, client)
            except Exception as exc:
                logger.exception("Classification failed for document %d", document.pk)
                document.status = Status.FAILED
                document.error_message = f"Classification failed: {exc}"
                await document.asave(
                    update_fields=["status", "error_message", "updated_at"]
                )
                yield sse_event("error", {"step": "classify", "message": str(exc)})
                return

            document.doc_type = doc_type
            await document.asave(update_fields=["doc_type", "updated_at"])
            yield sse_event(
                "step_complete",
                {
                    "step": "classify",
                    "message": f"Document classified as '{doc_type}'.",
                    "doc_type": doc_type,
                },
            )

            # --- Stage 3: Extract structured data ---
            yield sse_event(
                "progress",
                {
                    "step": "extract",
                    "message": "Extracting structured data...",
                },
            )
            try:
                extracted = await extraction_agent.extract_structured_data(
                    raw_text, doc_type, client
                )
            except Exception as exc:
                logger.exception("Extraction failed for document %d", document.pk)
                document.status = Status.FAILED
                document.error_message = f"Extraction failed: {exc}"
                await document.asave(
                    update_fields=["status", "error_message", "updated_at"]
                )
                yield sse_event("error", {"step": "extract", "message": str(exc)})
                return

            yield sse_event(
                "step_complete",
                {
                    "step": "extract",
                    "message": "Structured data extracted.",
                },
            )

        # --- Stage 4: Validate (sync, no client needed) ---
        yield sse_event(
            "progress", {"step": "validate", "message": "Validating extracted data..."}
        )
        validated = validation_agent.validate(extracted, doc_type)
        confidence = validated.get("_validation", {}).get("confidence", 0.0)

        document.extracted_data = validated
        document.confidence = confidence
        document.status = Status.COMPLETED
        await document.asave(
            update_fields=[
                "extracted_data",
                "confidence",
                "status",
                "updated_at",
            ]
        )

        yield sse_event(
            "step_complete",
            {
                "step": "validate",
                "message": "Validation complete.",
                "confidence": confidence,
                "is_valid": validated["_validation"]["is_valid"],
            },
        )

        yield sse_event(
            "complete",
            {
                "document_id": document.pk,
                "status": "completed",
                "doc_type": document.doc_type,
                "confidence": confidence,
                "detail_url": f"/api/agents/documents/{document.pk}/",
            },
        )


# ---------------------------------------------------------------------------
# View 3: GET /api/agents/documents/<id>/
# ---------------------------------------------------------------------------

class DocumentDetailView(View):
    """
    Returns the fully processed document as JSON.
    """

    async def get(self, request, pk: int):
        try:
            document = await Document.objects.aget(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({"error": "Document not found."}, status=404)

        serializer = DocumentDetailSerializer(document)
        return JsonResponse(serializer.data, status=200)
