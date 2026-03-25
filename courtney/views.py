import json
from decimal import Decimal

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document, DocumentProcess
from .serializers import DocumentUploadSerializer, DocumentListSerializer, DocumentDetailSerializer
from .agents.landrecord.pipelines.graph import run_pipeline_stream
from .services.selection_service import select_process


class _DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class DocumentUploadView(APIView):
    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        return Response(
            {"slug": document.slug, "stream_url": f"/api/documents/{document.slug}/process/"},
            status=201,
        )


class DocumentListView(APIView):
    def get(self, request):
        documents = Document.objects.order_by("-created")
        serializer = DocumentListSerializer(documents, many=True)
        return Response(serializer.data)


class DocumentDetailView(APIView):
    def get(self, request, slug):
        document = get_object_or_404(
            Document.objects.prefetch_related(
                "processes",
                "processes__logs",
                "processes__logs__agent",
            ),
            slug=slug,
        )
        serializer = DocumentDetailSerializer(document, context={"request": request})
        return Response(serializer.data)


class DocumentSelectProcessView(APIView):
    def post(self, request, slug, process_slug):
        document = get_object_or_404(Document, slug=slug)
        process = get_object_or_404(DocumentProcess, slug=process_slug, document=document)
        land_record = select_process(process)
        return Response({"land_record_id": land_record.pk}, status=200)


class DocumentProcessDeleteView(APIView):
    def delete(self, request, slug, process_slug):
        document = get_object_or_404(Document, slug=slug)
        process = get_object_or_404(DocumentProcess, slug=process_slug, document=document)
        if process.is_selected:
            return Response(
                {"detail": "Cannot delete a selected process. Deselect it first."},
                status=400,
            )
        process.delete()
        return Response(status=204)


class DocumentProcessStreamView(View):
    async def get(self, request, slug):
        document = await Document.objects.aget(slug=slug)

        async def event_stream():
            async for event in run_pipeline_stream(document.pk):
                yield f"data: {json.dumps(event, cls=_DecimalEncoder)}\n\n"

        return StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
