from pathlib import Path

from rest_framework import serializers

from .models import Book, Record, Page


class RecordSerializer(serializers.ModelSerializer):
    pages = serializers.ListField(child=serializers.FileField(), write_only=True)

    class Meta:
        model = Record
        fields = ("uuid", "pages")
        read_only_fields = ("uuid",)

    def create(self, validated_data):
        pages_data = validated_data.pop("pages")
        record = Record.objects.create(**validated_data)
        for file in pages_data:
            Page.objects.create(record=record, file=file)
        return record


class BookCreateSerializer(serializers.Serializer):
    folder_path = serializers.CharField(max_length=1024)

    def validate_folder_path(self, value: str) -> str:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise serializers.ValidationError(f"Folder does not exist: {path}")
        if not path.is_dir():
            raise serializers.ValidationError(f"Path is not a directory: {path}")
        return str(path)


class BookStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "uuid",
            "name",
            "folder_path",
            "status",
            "total_records",
            "processed_records",
            "failed_records",
            "started_at",
            "finished_at",
            "error_message",
            "created",
            "updated",
        )
        read_only_fields = fields
