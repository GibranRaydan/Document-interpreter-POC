# core_project/api/views.py
from api.serializers import DocumentExtractionRequestSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import extract_document_data
import logging

logger = logging.getLogger(__name__)


class DocumentDataExtractionView(APIView):
    """
    Receives raw text and uses Ollama to return structured extracted data for land records.
    """

    def post(self, request, *args, **kwargs):
        serializer = DocumentExtractionRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        deed_text = serializer.validated_data["text"]
        model = serializer.validated_data["model"]

        try:
            result = extract_document_data(deed_text, model_name=model)
        except Exception as e:
            logger.exception("Error extracting document data with Ollama.")
            return Response(
                {"error": "Internal processing error.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if isinstance(result, dict) and result.get("error"):
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result, status=status.HTTP_200_OK)
