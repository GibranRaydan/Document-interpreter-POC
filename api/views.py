# core_project/api/views.py
from api.serializers import DocumentExtractionRequestSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import extract_document_data, extract_text_from_pdf
import logging

logger = logging.getLogger(__name__)


class DocumentDataExtractionView(APIView):
    """
    Receives a PDF file, extracts text using Tesseract OCR,
    and returns structured extracted data.
    """

    def post(self, request, *args, **kwargs):
        serializer = DocumentExtractionRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        pdf_file = serializer.validated_data["file"]
        model = serializer.validated_data["model"]

        try:
            pdf_bytes = pdf_file.read()

            # 1 OCR
            extracted_text = extract_text_from_pdf(pdf_bytes)
            print(extracted_text)

            if not extracted_text.strip():
                return Response(
                    {"error": "No text could be extracted from the PDF."},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

            # 2️ Existing extraction logic
            result = extract_document_data(extracted_text, model_name=model)

        except Exception as e:
            logger.exception("Error processing PDF document.")
            return Response(
                {"error": "Internal processing error.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if isinstance(result, dict) and result.get("error"):
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result, status=status.HTTP_200_OK)
