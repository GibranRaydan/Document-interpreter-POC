from django.db import models

from .enums import *


class Document(models.Model):
    file = models.FileField(upload_to="documents/%Y/%m/")
    slug = models.SlugField(unique=True, max_length=50)
    name = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=50, choices=DocumentType.choices, default=DocumentType.LAND_RECORD)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courtney_async_document"

    def __str__(self):
        return f"{self.get_type_display()} — {self.name or self.slug}"


class DocumentProcess(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="processes")
    slug = models.SlugField(unique=True)
    version = models.PositiveSmallIntegerField(default=1)
    step = models.CharField(max_length=50, blank=True, default="")
    raw_text = models.TextField(blank=True, default="")
    data = models.JSONField(null=True, blank=True)
    is_selected = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courtney_async_documentprocess"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["document"],
                condition=models.Q(is_selected=True),
                name="courtney_async_unique_selected_process_per_document",
            )
        ]
        verbose_name = "Document Process"
        verbose_name_plural = "Document Processes"

    def __str__(self):
        return f"Process v{self.version} [{self.step}] — {self.slug}"


class Agent(models.Model):
    name = models.CharField(max_length=100, unique=True)
    model = models.CharField(max_length=50, choices=LLMModels.choices)
    system_prompt = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courtney_async_agent"

    def __str__(self):
        return self.name


class ProcessLog(models.Model):
    process = models.ForeignKey(DocumentProcess, on_delete=models.CASCADE, related_name="logs")
    step = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=StepStatus.choices)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    detail = models.TextField(blank=True, default="")
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    tokens_input = models.PositiveIntegerField(null=True, blank=True)
    tokens_output = models.PositiveIntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "courtney_async_processlog"
        ordering = ["id"]

    def __str__(self):
        return f"{self.step} [{self.status}] — process {self.process_id}"


class LandRecord(models.Model):
    process = models.OneToOneField(DocumentProcess, on_delete=models.CASCADE, related_name="land_record")
    book = models.CharField(max_length=255, blank=True, null=True)
    page = models.CharField(max_length=255, blank=True, null=True)
    document_type = models.CharField(max_length=255, blank=True, null=True)
    page_range = models.CharField(max_length=255, blank=True, null=True)
    property_address = models.CharField(max_length=255, blank=True, null=True)
    legal_description = models.TextField(blank=True, null=True)
    consideration_amount = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    execution_date = models.DateField(blank=True, null=True)
    county = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courtney_async_landrecord"

    def __str__(self):
        return f"LandRecord — {self.property_address or self.pk}"


class Party(models.Model):
    land_record = models.ForeignKey(LandRecord, on_delete=models.CASCADE, related_name="parties")
    name = models.CharField(max_length=100, blank=True, null=True)
    givenname = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=7, choices=PartyRole.choices, blank=True, null=True)
    type = models.CharField(max_length=1, choices=PartyType.choices, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courtney_async_party"


class Reference(models.Model):
    land_record = models.ForeignKey(LandRecord, on_delete=models.CASCADE, related_name="references")
    book = models.CharField(max_length=255, blank=True, null=True)
    page = models.CharField(max_length=255, blank=True, null=True)
    document_type = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courtney_async_reference"
