from django.contrib import admin
from django.db import models

from django_json_widget.widgets import JSONEditorWidget

from .models import Book, Record, Page


class PageInline(admin.StackedInline):
    model=Page
    extra=0


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "created", "updated")
    formfield_overrides = {models.JSONField: {"widget": JSONEditorWidget(mode="code",)}}
    inlines = (PageInline,)


class RecordInline(admin.StackedInline):
    fields = ("book_start_page", "status")
    readonly_fields = ("book_start_page", "status",)
    model=Record
    extra=0
    show_change_link = True


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "name", "folder_path", "created", "updated")
    formfield_overrides = {models.JSONField: {"widget": JSONEditorWidget(mode="code",)}}
    inlines = (RecordInline,)