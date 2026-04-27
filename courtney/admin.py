from django.contrib import admin
from django.db import models

from django_json_widget.widgets import JSONEditorWidget

from .models import Record, Page


class PageInline(admin.StackedInline):
    model=Page
    extra=0


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "created", "updated")
    formfield_overrides = {models.JSONField: {"widget": JSONEditorWidget(mode="code",)}}
    inlines = (PageInline,)
