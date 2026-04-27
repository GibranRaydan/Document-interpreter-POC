import uuid

from django.db import models
from django.core.validators import FileExtensionValidator


class Book(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.uuid}"


class Record(models.Model):
    book = models.ForeignKey(Book, related_name="records", on_delete=models.CASCADE, null=True, blank=True)
    data = models.JSONField(blank=True, default=dict)
    trace_id = models.CharField(max_length=255, null=True, blank=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.uuid}"


class Page(models.Model):
    record = models.ForeignKey(Record, related_name="pages", on_delete=models.CASCADE)
    file = models.FileField(validators=[FileExtensionValidator(allowed_extensions=["pdf", "tiff", "tif", "png", "jpg", "jpeg"])])
    raw_text = models.TextField(blank=True, default="")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.uuid}"
