from django.db import models


class DocumentType(models.TextChoices):
    LAND_RECORD = "land_record", "Land Record"


class StepStatus(models.TextChoices):
    STARTED = "started", "Started"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class LLMModels(models.TextChoices):
    LLAMA3_1 = "llama3.1", "Llama 3.1"
    LLAMA3_2_VISION = "llama3.2-vision", "Llama 3.2 Vision"
    MINICPM_V = "minicpm-v", "MiniCPM v1"
    GPT_OSS = "gpt-oss", "GPT-OSS"
    GLM_OCR = "glm-ocr", "GLM-OCR"


class PartyRole(models.TextChoices):
    GRANTOR = "GRANTOR", "Grantor"
    GRANTEE = "GRANTEE", "Grantee"


class PartyType(models.TextChoices):
    F = "F", "Firm"
    I = "I", "Individual"