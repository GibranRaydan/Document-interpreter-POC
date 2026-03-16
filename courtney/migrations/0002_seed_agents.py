from django.db import migrations

DEFAULT_AGENTS = [
    {
        "name": "ocr",
        "model": "minicpm-v",
        "system_prompt": (
            "You are an OCR engine. Extract ALL visible text from the provided image. "
            "Return only the extracted text with no additional commentary, formatting, "
            "or explanation. Preserve line breaks as they appear in the image."
        ),
    },
    {
        "name": "classifier",
        "model": "llama3.1",
        "system_prompt": (
            "You are a document classifier for land records. "
            "Given the text of a document, classify it into exactly one of these categories: "
            "deeds, mortgages, releases, liens, assignments, other. "
            "Respond with ONLY the category name in lowercase. "
            "Do not include any other text, punctuation, or explanation."
        ),
    },
    {
        "name": "extractor",
        "model": "llama3.1",
        "system_prompt": (
            "You are a structured data extraction engine for land record documents. "
            "Extract all relevant fields and return ONLY a valid JSON object. "
            "Do not include any explanation or markdown. Return raw JSON only."
        ),
    },
    {
        "name": "validator",
        "model": "llama3.1",
        "system_prompt": "",
    },
]


def seed_agents(apps, schema_editor):
    Agent = apps.get_model("courtney", "Agent")
    for data in DEFAULT_AGENTS:
        Agent.objects.get_or_create(name=data["name"], defaults=data)


def unseed_agents(apps, schema_editor):
    Agent = apps.get_model("courtney", "Agent")
    Agent.objects.filter(name__in=[d["name"] for d in DEFAULT_AGENTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("courtney", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_agents, reverse_code=unseed_agents),
    ]
