from django.contrib import admin

from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from.enums import *
from .models import Agent, Document, DocumentProcess, LandRecord, ProcessLog


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "updated")
    search_fields = ("name",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "created")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(DocumentProcess)
class DocumentProcessAdmin(admin.ModelAdmin):
    list_display = ("slug", "document", "version", "step", "is_selected", "created")
    list_filter = ("step", "is_selected")
    search_fields = ("slug",)
    readonly_fields = ("slug", "created", "updated")
    formfield_overrides = {models.JSONField: {"widget": JSONEditorWidget(mode="view")}}


@admin.register(LandRecord)
class LandRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "property_address", "document_type", "execution_date", "county", "state")
    search_fields = ("property_address", "legal_description", "county")
    list_filter = ("document_type", "state")


@admin.register(ProcessLog)
class ProcessLogAdmin(admin.ModelAdmin):
    list_display = ("process", "step", "status", "tokens_input", "tokens_output", "duration_ms", "created")
    list_filter = ("step", "status")
    readonly_fields = ("created",)
