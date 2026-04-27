from rest_framework import serializers

from .models import Record, Page


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
