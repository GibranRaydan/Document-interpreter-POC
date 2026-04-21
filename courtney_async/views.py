import uuid

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Document
from .serializers import ALLOWED_EXTENSIONS
from .temporal.client import get_temporal_client
from .temporal.workflows.landrecord_workflow import LandRecordWorkflow


@method_decorator(csrf_exempt, name="dispatch")
class DocumentUploadAndProcessView(View):
    async def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return JsonResponse({"error": "No file provided."}, status=400)

        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return JsonResponse(
                {"error": f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"},
                status=400,
            )

        slug = slugify(str(uuid.uuid4()))[:50]
        document = await Document.objects.acreate(
            file=file,
            slug=slug,
            name=file.name,
        )

        client = await get_temporal_client()
        handle = await client.start_workflow(
            LandRecordWorkflow.run,
            document.pk,
            id=f"landrecord-{document.slug}",
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )

        return JsonResponse(
            {
                "document_slug": document.slug,
                "workflow_id": handle.id,
                "temporal_ui": f"http://localhost:8080/namespaces/default/workflows/{handle.id}",
            },
            status=202,
        )
