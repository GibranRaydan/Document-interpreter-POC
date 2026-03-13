from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "doc_type", "confidence", "created_at")
    list_filter = ("status", "doc_type")
    readonly_fields = ("created_at", "updated_at", "raw_text",)
    search_fields = ("doc_type", "error_message")
    formfield_overrides = {models.JSONField: {"widget": JSONEditorWidget(mode="view")}}
