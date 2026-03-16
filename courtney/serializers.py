import uuid

from django.utils.text import slugify
from rest_framework import serializers

from .models import Agent, Document, DocumentProcess, LandRecord, ProcessLog


class AgentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ["name", "model"]


class ProcessLogSerializer(serializers.ModelSerializer):
    agent = AgentSummarySerializer(read_only=True)

    class Meta:
        model = ProcessLog
        fields = ["step", "status", "agent", "detail", "duration_ms", "tokens_input", "tokens_output", "created"]


class DocumentProcessSerializer(serializers.ModelSerializer):
    logs = ProcessLogSerializer(many=True, read_only=True)
    land_record_id = serializers.SerializerMethodField()

    class Meta:
        model = DocumentProcess
        fields = ["slug", "version", "step", "is_selected", "land_record_id", "data", "created", "updated", "logs"]

    def get_land_record_id(self, obj):
        try:
            return obj.land_record.pk
        except LandRecord.DoesNotExist:
            return None


class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["slug", "name", "type", "created"]


class DocumentDetailSerializer(serializers.ModelSerializer):
    processes = DocumentProcessSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ["slug", "name", "type", "file", "created", "updated", "processes"]


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["slug", "file", "name", "type", "created"]
        read_only_fields = ["slug", "created"]

    def create(self, validated_data):
        validated_data["slug"] = slugify(str(uuid.uuid4()))[:50]
        if not validated_data.get("name"):
            validated_data["name"] = validated_data["file"].name
        return super().create(validated_data)
