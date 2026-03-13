from django.db import models


class Status(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Document(models.Model):

    # file: accepts both images and PDFs — no type restriction yet
    file = models.FileField(upload_to="documents/%Y/%m/")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # doc_type: free text, no choices defined yet — the classifier agent sets this
    doc_type = models.CharField(max_length=50, blank=True, default="")
    raw_text = models.TextField(blank=True, default="")
    extracted_data = models.JSONField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Document #{self.pk} [{self.status}]"
