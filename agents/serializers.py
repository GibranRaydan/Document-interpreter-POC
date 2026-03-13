from rest_framework import serializers
from .models import Document


class DocumentUploadSerializer(serializers.ModelSerializer):
    """
    Used for POST /documents/ — accepts only the file (PDF or image).
    Status defaults to 'pending' in the model; all other fields are
    read-only or system-generated.
    """
    class Meta:
        model = Document
        fields = ["file"]


class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Used for GET /documents/<id>/ — returns all computed fields.
    """
    class Meta:
        model = Document
        fields = [
            "id",
            "file",
            "status",
            "doc_type",
            "raw_text",
            "extracted_data",
            "confidence",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
