import uuid

from django.db import models
from django.core.validators import FileExtensionValidator


BOOK_STATUS_CHOICES = [
    ("pending", "pending"),
    ("scanning", "scanning"),
    ("processing", "processing"),
    ("completed", "completed"),
    ("failed", "failed"),
]


RECORD_STATUS_CHOICES = [
    ("pending", "pending"),
    ("processing", "processing"),
    ("completed", "completed"),
    ("failed", "failed"),
]


class Book(models.Model):
    folder_path = models.CharField(max_length=1024, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=20, default="pending", choices=BOOK_STATUS_CHOICES)
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name or self.uuid}"


class Record(models.Model):
    book = models.ForeignKey(Book, related_name="records", on_delete=models.CASCADE, null=True, blank=True)
    book_start_page = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default="pending", choices=RECORD_STATUS_CHOICES)
    trace_id = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(blank=True, default=dict)
    error_message = models.TextField(blank=True, default="")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.uuid}"


class Page(models.Model):
    record = models.ForeignKey(Record, related_name="pages", on_delete=models.CASCADE)
    file = models.FileField(
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "tiff", "tif", "png", "jpg", "jpeg"])],
    )
    file_path = models.CharField(max_length=1024, blank=True, default="")
    page_number = models.IntegerField(null=True, blank=True)
    raw_text = models.TextField(blank=True, default="")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page_number", "id"]

    def __str__(self):
        return f"{self.uuid}"
